# iotpubsub (Internet of Things Publish/Subscribe)

This package consists of two main items.  First, the *mosquitto* directory contains what you need to get a Mosquitto MQTT broker running either on a system or Docker image.  Second, the *MQTTClient* class provides an abstraction of the *paho.mqtt.Client* class, which will allow you to interact with the broker in Python.

## Mosquitto setup

### install on the system



### Docker image

Both [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) need to be installed.  As of 2024-10-19, Docker have support for Pi 64-bit, however, I had luck using the [1_setup_docker_apt_repo](https://github.c/blob/main/configs/docker/1_setup_docker_apt_repo.sh) in the *slowrunner/wali_pi5* repo.  After execution of the script, issue `sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose docker-compose-plugin`.

The *mosquitto/docker-compose.yml* file along with the *mosquitto/mosquitto.conf* file have everything that's needed to build an image that when run will host a Mosquitto broker.  Copy the *mosquitto* directory to another location outside of the repo.  This is done to preserve the correct status of the repo.  If a docker image were built using the docker compose file in the mosquitto directory, this repo would be somewhat contaminated due to the build's alteration of permissions of files and directories in the repo.  Change directory to the copy of the *mosquitto* directory and issue 
`docker-compose up --detach` to build the image.  Notice that after the image has been built, ownership of this copied mosquitto directory will hve recursively been changed to user *1883*, which is the *mosquitto* user' UID.  If the build fails or the container doesn't start, use `docker-compose ps mosquitto` to view the build log, make a fix (you'll need sudo 
to edit files since they're no longer owned by you) and execute *rebuild_image.sh* (don't forget to make this an executable file first) to have another go at building the image and running the container.  After building an image, it'll be running if everything was successful.  Use `docker ps` to verify the status.

### authentication

#### password-based

At this point, you have a broker that'll accept any client on its port 1883 without any kind of authentication of the client.  We can use the MQTTClient class to verify this if desired.  Use `sudo tail -F log/mosquitto.log` to keep an eye on the broker's log then use the commands below to connect to the broker.  In the log, you'll see `2025-02-22-12:04:27: Sending PINGRESP to test_client` to indicate that the broker is allowing the client's connection.
```python
import iotpubsub
client = iotpubsub.MQTTClient(client_id='test_client', broker_ip=<broker IP address>, broker_port=1883)
```

If you want to use password-based authentication, you can add a password for a user with `mosquitto_passwd -c /mosquitto/config/.passwords <username>`, where *username* is the name of a person or service (that's unique to the broker) that'll be connecting to the broker.  If the broker is in a container, you'll need to attach it with `docker exec -it mosquitto sh` before executing the command.  You'll now see the username and a hash of their password in */mosquitto/config/. passwords*.  
Change `allow_anonymous true` to `false` and uncomment `#password_file /mosquitto/config/.passwords` in `/mosquitto/config/mosquitto.conf` and restart the service or container to enable password-based authentication.  Try connecting with the code below.  If you attempt to connect without using the correct username/password combination you'll see a `Client test_client disconnected, not authorised.` in the broker's log.
```python
from iotpubsub import MQTTClient
client = MQTTClient(client_id='test_client', broker_ip='192.168.1.103', broker_port=1883, username=<username>, password=<password>)
```
Use `mosquitto_passwd -b /mosquitto/config/.passwords <username>` to add users and `mosquitto_passwd -D /mosquitto/config/.passwords <username>` to remove them.  If the broker is in a container, issue `kill -HUP <process id of mosquitto>` to restart the broker after adding and/or removing users.

#### certificate based

X.509 certificates may be used to authenticate the client and broker to one another.  When used they also encrypt payloads from publisher to broker and from broker to subscriber.  When the directive `require_certificate true` is in the .conf file, a client needs to present its certificate to the broker, which then verifies it against the certificate of the CA defined in the `cafile` option.

This will make both CA certificate and a key for the CA.
```shell
 openssl req -nodes -x509 -newkey rsa:4096 -keyout my-ca-key.pem -out my-ca.crt -days 356

-----
Country Name (2 letter code) [AU]:US
State or Province Name (full name) [Some-State]:Michigan
Locality Name (eg, city) []:Ann Arbor
Organization Name (eg, company) [Internet Widgits Pty Ltd]:Example University
Organizational Unit Name (eg, section) []:IT
Common Name (e.g. server FQDN or YOUR name) []:Root CA
Email Address []:rosbrian@umich.edu
```

Make a CSR for the client.  The CN=demo-client sets the Common Name.  This CN will be used as the username in the directive `use_identity_as_username true` in the .conf
