# iotpubsub (Internet of Things Publish/Subscribe)

This package consists of two main items.  First, the *mosquitto* directory contains what you need to get a Mosquitto MQTT broker running either on a system or Docker image.  Second, the *MQTTClient* class provides an abstraction of the *paho.mqtt.Client* class, which will allow you to interact with the broker in Python.

## Mosquitto setup

### install on the system



### Docker image

Both [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) need to be installed.  As of 2024-10-19, Docker have support for Pi 64-bit, however, I had luck using the [1_setup_docker_apt_repo](https://github.c/blob/main/configs/docker/1_setup_docker_apt_repo.sh) in the *slowrunner/wali_pi5* repo.  After execution of the script, issue `sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose docker-compose-plugin`.

The *mosquitto/docker-compose.yml* file along with the *mosquitto/mosquitto.conf* file have everything that's needed to build an image that when run will host a Mosquitto broker.  Change directory to the *mosquitto* directory and issue `docker-compose up --detach` to build the image.  Notice that after the image has been built, ownership of the mosquitto directory has recursively been changed to user *1883*, which is the *mosquitto* user' UID.  If the build fails or the container doesn't start, use `docker-compose ps mosquitto` to view the build log, make a fix (you'll need sudo 
to edit files since they're no longer owned by you) and execute *rebuild_image.sh* (don't forget to make this an executable file first) to have another go at building the image and running the container.  After building an image, it'll be running if everything was successful.  Use `docker ps` to verify the status.

### additional setup

At this point, you have a broker that'll accept any client on its port 1883 without any kind of authentication of the client.  We can use the MQTTClient class to verify this using:
```python
import iotpubsub

```
