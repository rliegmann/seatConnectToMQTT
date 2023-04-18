#!/usr/bin/env python3
import pprint
import asyncio
import logging
import inspect
import time
import sys
import os
import json
import random

import paho.mqtt.client as mqtt
broker_address= os.environ.get('MQTT_BROKER_SERVER')
topic = os.environ.get('MQTT_BROKER_TOPIC')
from aiohttp import ClientSession
from datetime import datetime

from OSMPythonTools.nominatim import Nominatim

#import schedule

logging.getLogger('OSMPythonTools').setLevel(logging.ERROR)
nominatim = Nominatim()


#import debugpy;
#debugpy.listen(("0.0.0.0", 5678))

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

try:
    from seatconnect import Connection
except ModuleNotFoundError as e:
    print(f"Unable to import library: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

USERNAME = os.environ.get('SEAT_CONNECT_USER')
PASSWORD = os.environ.get('SEAT_CONNECT_PASS')
PRINTRESPONSE = True
INTERVAL = int(os.environ.get('SETTINGS_INTERVAL'))
OPENHAB_USE = bool(os.environ.get('SETTINGS_OPENHAB_USE'))
SETTINGS_ADDRESS_LOOKUP = bool(os.environ.get('SETTINGS_ADDRESS_LOOKUP'))

COMPONENTS = {
    'sensor': 'sensor',
    'binary_sensor': 'binary_sensor',
    'lock': 'lock',
    'device_tracker': 'device_tracker',
    'switch': 'switch',
}

RESOURCES = [
		"adblue_level",
		"auxiliary_climatisation",
		"battery_level",
		"charge_max_ampere",
		"charger_action_status",
		"charging",
        "charge_rate",
        "charging_power",
		"charging_cable_connected",
		"charging_cable_locked",
		"charging_time_left",
		"climater_action_status",
		"climatisation_target_temperature",
		"climatisation_without_external_power",
		"combined_range",
		"combustion_range",
        "departure1",
        "departure2",
        "departure3",
		"distance",
		"door_closed_left_back",
		"door_closed_left_front",
		"door_closed_right_back",
		"door_closed_right_front",
		"door_locked",
		"electric_climatisation",
		"electric_range",
		"energy_flow",
		"external_power",
		"fuel_level",
		"hood_closed",
		"last_connected",
		"lock_action_status",
		"oil_inspection",
		"oil_inspection_distance",
        "oildisplay_0",
		"outside_temperature",
		"parking_light",
		"parking_time",
		"pheater_heating",
		"pheater_status",
		"pheater_ventilation",
		"position",
		"refresh_action_status",
		"refresh_data",
        "request_flash",
        "request_honkandflash",
		"request_in_progress",
		"request_results",
		"requests_remaining",
		"service_inspection",
		"service_inspection_distance",
		"sunroof_closed",
		"trip_last_average_auxillary_consumption",
		"trip_last_average_electric_consumption",
		"trip_last_average_fuel_consumption",
		"trip_last_average_speed",
		"trip_last_duration",
		"trip_last_entry",
		"trip_last_length",
		"trip_last_recuperation",
		"trip_last_total_electric_consumption",
		"trunk_closed",
		"trunk_locked",
		"vehicle_moving",
		"window_closed_left_back",
		"window_closed_left_front",
		"window_closed_right_back",
		"window_closed_right_front",
		"window_heater",
		"windows_closed",
        "seat_heating"
]

def prepareOpenhab(instrument):
    if instrument.component == "sensor":
        if instrument.device_class == "timestamp":
            timestamp = datetime.strptime(instrument.state, '%Y-%m-%d %H:%M:%S')
            return timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        return instrument.state
    if instrument.component == "binary_sensor":
        if instrument.device_class == "lock":
            return "Locked" if instrument.state else "Unlocked"              
        return instrument.state
    if instrument.component == "lock":        
        return "Locked" if instrument.state else "Unlocked"
    if instrument.component == "device_tracker":
        return str(instrument.state[0]) + ',' + str(instrument.state[1])
    if instrument.component == "switch":
        return instrument.state
    

def is_enabled(attr):
    """Return true if the user has enabled the resource."""
    #return attr in RESOURCES
    return True

def isString(value):
    return value if isinstance(value, str) else ""

def positionToAddress(lat, lon):
    """Returns die Address for GPS. Use openStreetMap for this""" 
    # = Nominatim()
    #  48.10146°N 11.520163
    #lat = random.randint(48000, 49000)
    #lon = random.randint(11000, 12000)
    try:
        result = nominatim.query(lat, lon, reverse=True, zoom=18)
        data = result.address()
        
        
        if 'house_number' in data:
            house_number = isString(data['house_number'])
        else:
            house_number = ""
            
        if 'city' in data:
            city = isString(data['city'])
        elif 'village' in data:
            city = isString(data['village'])           
            
            
            
        return isString(data['road']) + " " + house_number + ", " + isString(data['postcode']) + " " + city
    except Exception as ex: 
        print('Error: OSM reqest')
        print(ex)
        return ""
    
    

async def runSeatConnect():
    client =  mqtt.Client("P1") #Test
    client.connect(broker_address) #Test
    lastUpdate = datetime.now()

    async with ClientSession(headers={'Connection': 'keep-alive'}) as session:
        print('')
        print('########################################')
        print('#      Logging on to Seat Connect     #')
        print('########################################')
        print(f"Initiating new session to Seat Connect with {USERNAME} as username")
        connection = Connection(session, USERNAME, PASSWORD, PRINTRESPONSE)
        print("Attempting to login to the Seat Connect service")
        print(datetime.now())
        if await connection.doLogin():
            print('Login success!')
            print(datetime.now())
            print('Fetching vehicles associated with account.')
            await connection.get_vehicles()

            instruments = set()
            for vehicle in connection.vehicles:
                txt = vehicle.vin
                print('')
                print('########################################')
                print('#         Setting up dashboard         #')
                print(txt.center(40, '#'))
                dashboard = vehicle.dashboard(mutable=True)
                print("------------------------------------------------------")
                print(dashboard.instruments)
                print("------------------------------------------------------")

                for instrument in (
                        instrument
                        for instrument in dashboard.instruments
                        if instrument.component in COMPONENTS
                        or is_enabled(instrument.slug_attr)):

                    instruments.add(instrument)
            print('')
            print('########################################')
            print('#          Vehicles discovered         #')
            print('########################################')
            for vehicle in connection.vehicles:
                print(f"\tVIN: {vehicle.vin}")
                print(f"\tModel: {vehicle.model}")
                print(f"\tManufactured: {vehicle.model_year}")
                print(f"\tConnect service deactivated: {vehicle.deactivated}")
                print("")
                if vehicle.is_nickname_supported: print(f"\tNickname: {vehicle.nickname}")
                #print(f"\tObject attributes, and methods:")
                #for prop in dir(vehicle):
                #    if not "__" in prop:
                #        try:
                #            func = f"vehicle.{prop}"
                #            typ = type(eval(func))
                #            print(f"\t\t{prop} - {typ}")
                #        except:
                #            pass

        else:
            return False

        # Output all instruments and states
        print('')
        print('########################################')
        print('#      Instruments from dashboard      #')
        print('########################################')        
        inst_list = sorted(instruments, key=lambda x: x.attr)
        jsonToSend = {}
        openhabToSend = {}
        jsonToSend['last_update'] = lastUpdate.strftime("%Y-%m-%dT%H:%M:%S")
        for instrument in inst_list:
            print(f'{instrument.full_name} - {instrument.str_state} - attributes: {instrument.attributes}')
            TROPIC = topic + "/single/" + format(instrument.attr)
            PAYLOD = format(instrument.str_state)            
            
            client.publish(TROPIC,PAYLOD,0,True)
            time.sleep(0.01)
            
            #data = {}
            #data[format(instrument.attr)] = instrument.str_state
            #jsonToSend.append(data)
            jsonToSend[format(instrument.attr)] = instrument.str_state
            if OPENHAB_USE:
                client.publish(topic + "/openhab/" + format(instrument.attr), prepareOpenhab(instrument), 0, True)
                time.sleep(0.01)
                
        #rawPositionsData = [x for x in inst_list if x.attr == 'position']
        #if rawPositionsData:
        for rawPositionsData in [x for x in inst_list if x.attr == 'position']:
            print("exist")
            if SETTINGS_ADDRESS_LOOKUP:   
                if rawPositionsData.state[0] == 'None' or rawPositionsData.state[1]  == 'None':    # Vehicle is moving
                    parkingAddress = positionToAddress(rawPositionsData.state[0], rawPositionsData.state[1])
                    jsonToSend['parking_address'] = parkingAddress
                    client.publish(topic + "/single/parking_address", parkingAddress, 0, True)
                    time.sleep(0.01)
                    client.publish(topic + "/openhab/parking_address", parkingAddress, 0, True)
                    time.sleep(0.01)
                 
         
        json_data = json.dumps(jsonToSend)           
        client.publish(topic + "/json",json_data,0,True)  
        time.sleep(1.01) 
        client.publish(topic + "/single/last_update", lastUpdate.strftime("%Y-%m-%dT%H:%M:%S"), 0, True)  
        time.sleep(1.01) 
        if OPENHAB_USE:
            client.publish(topic + "/openhab/last_update", lastUpdate.strftime("%Y-%m-%dT%H:%M:%S"), 0, True)
            time.sleep(1.01)
               
       
      
async def main():
    """Main method."""    
    while True:
        await runSeatConnect()
        await asyncio.sleep(INTERVAL)
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
