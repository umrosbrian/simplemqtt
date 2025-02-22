# iotpubsub (Internet of Things Publish/Subscribe)

This package consists of two main items.  First, the *mosquitto* directory contains what you need to get a Mosquitto MQTT broker running either on a system or Docker image.  Second, the *MQTTClient* class provides an abstraction of the *paho.mqtt.Client* class, which will allow you to interact with the broker in Python.

## Mosquitto setup

### install on the system



### Docker image

The *mosquitto/docker-compose.yml* file along with the *mosquitto/mosquitto.conf* file have everything that's needed to build an image that when run will host a Mosquitto broker.