# simple-mqtt

This package is intended to get a Mosquitto MQTT broker running and to provide the MQTTClient class that may be used to publish and/or subscribe to topics on the broker using bidirectional encryption.  The *mosquitto* directory has everything needed to get a broker running either on a system or in a Docker container.  In describing the setup of the broker, you'll see some examples of how the MQTTClient class is used.

To get started, clone this repo to a machine that will be used to host the broker.  After you've followed the instructions in either *install on the system* or *Docker image* sections to get a broker running, I recommend that you follow the *password-based authentication* section if you're unfamiliar with Mosquitto and/or MQTT before moving to the *certificate-based authentication and encryption* section.  After the broker is configured to use bidirectional encryption, we'll move focus to using clients. 

## Mosquitto MQTT broker

### install on the system



### Docker image

First off, both [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) need to be installed.  As of 2024-10-19, Docker doesn't have support for Pi 64-bit, however, I had luck using the [1_setup_docker_apt_repo](https://github.c/blob/main/configs/docker/1_setup_docker_apt_repo.sh) script in the *slowrunner/wali_pi5* repo to get it installed on a Pi running that OS.  After execution of the script, issue `sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose docker-compose-plugin`.

The *mosquitto/docker-compose.yml* file along with the *mosquitto/mosquitto.conf* file have what's needed to build an image that when run will host a Mosquitto broker.  Copy the *mosquitto* directory to another location outside the repo before building the image.  This is done to preserve the correct structure of the repo.  If a docker image were built using the docker compose file in the mosquitto directory, the repo would be somewhat contaminated due to the build's alteration of permissions of files and directories.  Change directory to the copy of the *mosquitto* directory and issue `docker-compose up --detach` to build the image.  Notice that after the image has been built, ownership of this copied mosquitto directory will have recursively been changed to user *1883*, which is the *mosquitto* user's UID.  If the build fails or the container doesn't start, use `docker-compose ps mosquitto` to view the build log, make a fix (you'll need sudo to edit files since they're no longer owned by you) and execute *<copy of mosquitto directory>/scripts/rebuild_image.sh* (don't forget to make this an executable file first) to have another go at building the image and running the container.  After building an image, it'll be running if everything was successful.  Use `docker ps` to verify the status.

### authentication

#### password-based authentication

At this point, you have a broker that'll accept any client on its port 1883 without any kind of authentication of the client.  We can use the MQTTClient class to verify this if desired.  Use `sudo tail -F log/mosquitto.log` to keep an eye on the broker's log then use the commands below to connect to the broker.  In the log, you'll see `2025-02-22-12:04:27: Sending PINGRESP to test_client` to indicate that the broker is allowing the client's connection.
```python
import simplemqtt
client = simplemqtt.MQTTClient(client_id='foo', broker_ip=<broker IP address>, broker_port=1883)
```
If you want to use password-based authentication, you can create a password file add a password for a user with `mosquitto_passwd -c /mosquitto/config/.passwords <username>`, where *username* is the name of a person or service that'll be connecting to the broker.  If the broker is in a container, you'll need to attach it with `docker exec -it mosquitto sh` before executing the command.  You'll now see the username and a hash of their password in */mosquitto/config/.passwords*. Change `allow_anonymous true` to `false` and uncomment `#password_file /mosquitto/config/.passwords` in `/mosquitto/config/mosquitto. conf` and restart the service or container to enable password-based authentication.  Try connecting with the code below.
```python
from simplemqtt import MQTTClient
client = MQTTClient(client_id='foo', broker_ip='192.168.1.103', broker_port=1883, username=<username>, password=<password>)
```
If you attempt to connect without using the correct username and/or password you'll see a `Client foo disconnected, not authorised.` in the broker's log.  Use `mosquitto_passwd -b /mosquitto/config/.passwords <username> <password>` to add users and `mosquitto_passwd -D /mosquitto/config/.passwords <username>` to remove them.  If the broker is in a container, issue `kill -HUP <process id of mosquitto>` when attached to the container or simply restart the container with `docker restart mosquitto` to restart the broker after adding and/or removing users.

At this point, you have a broker that'll accept only known users, but the payloads aren't protected in any way.  In the next section, we'll configure the broker to use bidirectional encryption.

#### certificate-based authentication and encryption

SSL/TLS types of X.509 certificates may be used to authenticate a client along with encrypting payloads from both a client acting as a publisher to the broker and from the broker to a client acting as a subscriber.  The first step we'll take to enable the use of certificates is executing `mosquitto/scripts/create_signing_CA.sh` to create a self-signed CA (Certificate Authority) we'll call the *root* CA which is the used to sign the CSR (Certificate Signing Request) of another CA, which we'll call the *signing* CA, to produce a certificate for the later. Then next step is to execute `mosquitto/scripts/create_server_key_and_certificate. sh` to have the signing CA sign the server's CSR to make a certificate for the server along with making a public key for the server.  You'll need to provide the server's IP address as an argument to this script, which will be added to the server's certificate.  These two scripts will produce the root CA's certificate (*rootCA.crt*), the server's certificate (*server.crt*) and server's key (*server.key*) that will be added to the mosquitto.conf file.  Note that these two scripts only need to be executed one time per broker server.

Uncomment all remaining lines in mosquitto.conf and provide the path to the path to the *rootCA.crt*, *server.crt* and *server.key* files for the *cafile*, *certfile* and *keyfile* directives, respectively.  Restart the broker or container to have the changes take effect.

# MQTTClient class

## certificate-based authentication and encryption

The creation of the client's certificate and public key are similar to what was done with the server.  However, you may want multiple clients and if so, will be creating a certificate and public key.  For now, let's just get one client up and running.  Execute `mosquitto/scripts/create_client_key_certificate_and_chain.sh` to create *client.crt* and *client.key* in the *client_certs* directory.  There will also be a *chain.crt* file created, which provides provenance of the client's certificate.  These three file are what's needed to both authenticate a client and provide encryption.  The 
code below shows how to use them with the MQTTClient class.
```python
import simplemqtt
client = simplemqtt.MQTTClient(broker_ip=<broker IP address>,
                              broker_port=8883,
                              cert_chain=<path to chain.crt>,
                              cert=<path to client.crt>,
                              key=<path to client.key>)
```
