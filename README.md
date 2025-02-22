# iotpubsub (Internet of Things Publish/Subscribe)

This package consists of two main items.  First, the *mosquitto* directory contains what you need to get a Mosquitto MQTT broker running either on a system or Docker image.  Second, the *MQTTClient* class provides an abstraction of the *paho.mqtt.Client* class, which will allow you to interact with the broker in Python.

## Mosquitto setup

### install on the system



### Docker image

Both [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) need to be installed.  As of 2024-10-19, Docker have support for Pi 64-bit, however, I had luck using the [1_setup_docker_apt_repo](https://github.c/blob/main/configs/docker/1_setup_docker_apt_repo.sh) in the *slowrunner/wali_pi5* repo.  After execution of the script, issue `sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose docker-compose-plugin`.

The *mosquitto/docker-compose.yml* file along with the *mosquitto/mosquitto.conf* file have everything that's needed to build an image that when run will host a Mosquitto broker.  Copy the *mosquitto* directory to another location outside of the repo.  This is done to preserve the correct status of the repo.  If a docker image were built using the docker compose file in the mosquitto directory, this repo would be somewhat contaminated due to the build's alteration of permissions of files and directories in the repo.  Change directory to the copy of the *mosquitto* directory and issue 
`docker-compose up --detach` to build the image.  Notice that after the image has been built, ownership of this copied mosquitto directory will hve recursively been changed to user *1883*, which is the *mosquitto* user' UID.  If the build fails or the container doesn't start, use `docker-compose ps mosquitto` to view the build log, make a fix (you'll need sudo 
to edit files since they're no longer owned by you) and execute *rebuild_image.sh* (don't forget to make this an executable file first) to have another go at building the image and running the container.  After building an image, it'll be running if everything was successful.  Use `docker ps` to verify the status.

### additional setup

At this point, you have a broker that'll accept any client on its port 1883 without any kind of authentication of the client.  We can use the MQTTClient class to verify this if desired.  Use `sudo tail -F log/mosquitto.log` to keep an eye on the broker's log then use the commands below to connect to the broker.  In the log, you'll see `2025-02-22-12:04:27: Sending PINGRESP to test_client` to indicate that the broker is allowing the client's connection.
```python
import iotpubsub
client = iotpubsub.MQTTClient(client_id='test_client', broker_ip=<broker IP address>, broker_port=1883)
```

If you want to use password-based authentication, you can add a password for a client with `mosquitto_passwd -c /mosquitto/config/.passwords <client name>`, where *client name* is unique to a client that'll be connecting to the broker.  If the broker is in a container, you'll need to attach it with `docker exec -it mosquitto sh` before executing the command.  You'll now see the client and a hash of the password in */mosquitto/config/. passwords*.  
Change `allow_anonymous true` to `false` and uncomment `#password_file /mosquitto/config/.passwords` in `/mosquitto/config/mosquitto.conf` and restart the service or container to enable password-based authentication.
```python
from iotpubsub import MQTTClient
client = MQTTClient(client_id='test_client', broker_ip='192.168.1.103', broker_port=1883, username=<username>, password=<password>)
```
If you attempt to connect without using the correct username/password combination you'll see a `Client test_client disconnected, not authorised.` in the broker's log.
