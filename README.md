# seatConnectToMQTT
Send Seat Connect Data to MQTT :-)


## MQTT
At the end of the queries, the script sends various MQTT messages to the broker. The following settings can be set using the environment variables:

| ENV variable |  Require | Description |
|--------------|----------|-------------------------|
|`MQTT_BROKER_SERVER` | yes | Mqtt Broker Address (192.168.0.100 or myBrocker.de) |
|`MQTT_BROKER_PORT`   | yes | Mqtt Broker Port (Default: 1883) |
|`MQTT_BROKER_USER`   | no  | Mqtt User (not used at the moment) |
|`MQTT_BROKER_PASS`   | no  | Mqtt Pass (not used at the moment) |



The following topics are played out:
| topic | Description |
|-------|-------------|
|`MQTT_BROKER_TOPIC/json`| Contains the data as a json blob |
|`MQTT_BROKER_TOPIC/openhab/..`| see openHAB section below |
|`MQTT_BROKER_TOPIC/single/...`| each individual data point as a separate topic |

## openHAP
If the environment variable **SETTINGS_OPENHAB_USE** is set to true, under the topic
`MQTT_BROKER_TOPIC/openhab/...`, every single data point formatted appropriately for openHAB. Especially the location.