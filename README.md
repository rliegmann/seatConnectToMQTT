# seatConnectToMQTT
Send Seat Connect Data to MQTT :-)


## MQTT

### openHAP
If the environment variable **SETTINGS_OPENHAB_USE** is set to true, under the topic
`MQTT_BROKER_TOPIC/openhab/...`, every single data point formatted appropriately for openHAB. Especially the location.