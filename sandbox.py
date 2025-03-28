import simplemqtt

# ----------------------------------------------------------------------------------------------------------------------
# test tls
# ----------------------------------------------------------------------------------------------------------------------
import paho.mqtt.client as mqtt
import ssl
from datetime import datetime as dt
from pydb import logging_to_console
logging_to_console()

def on_message(client, userdata, message):
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - topic: {message.topic}, payload: {message.payload.decode()}")

# start the subscriber in one console
sub = mqtt.Client(client_id='sub', callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# sub.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt")
sub.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt",
            certfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.crt",
            keyfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.key",
            tls_version=ssl.PROTOCOL_TLSv1_2)
sub.on_message = on_message
sub.connect(host='192.168.1.103', port=1883)
sub.subscribe('foo')
sub.loop_start()
# sub.loop_forever()  # use this if you have no intent of ever stopping the listening loop
sub.loop_stop()
sub.disconnect()

import paho.mqtt.client as mqtt
import ssl
# open another console and start a publisher
client = mqtt.Client(client_id='4711', callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# client.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt")
# I've found that a client can connect without any credentials, but can't do anything.  Maybe try adding
# 'allow_anonymous true' in the 8883 block of the .conf.
client.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt",
             certfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.crt",
             keyfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.key",
             tls_version=ssl.PROTOCOL_TLSv1_2)
client.connect(host='10.17.105.79', port=8883)
client.loop_start()
client.publish('foo', 'bar')
client.loop_stop()
client.disconnect()
# ----------------------------------------------------------------------------------------------------------------------
# use MQTTClient
# ----------------------------------------------------------------------------------------------------------------------
import ssl
from datetime import datetime as dt
from pydb import logging_to_console
logging_to_console()

def on_message(client, userdata, message):
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - topic: {message.topic}, payload: {message.payload.decode()}")

# start the subscriber in one console
sub = MQTTClient(client_id='sub', callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# sub.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt")
sub.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt",
            certfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.crt",
            keyfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.key",
            tls_version=ssl.PROTOCOL_TLSv1_2)
sub.on_message = on_message
sub.connect(host='10.17.105.79', port=8883)
sub.subscribe('foo')
sub.loop_start()
# sub.loop_forever()  # use this if you have no intent of ever stopping the listening loop
sub.loop_stop()
sub.disconnect()

import paho.mqtt.client as mqtt
import ssl
# open another console and start a publisher
client = MQTTClient(client_id='4711', callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# client.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt")
client.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt",
             certfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.crt",
             keyfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.key",
             tls_version=ssl.PROTOCOL_TLSv1_2)
client.connect(host='10.17.105.79', port=8883)
client.loop_start()
client.publish('foo', 'bar')
client.loop_stop()
client.disconnect()
# ----------------------------------------------------------------------------------------------------------------------
# try MQTTClient
# ----------------------------------------------------------------------------------------------------------------------
import simplemqtt
from datetime import datetime as dt

def cb(message):
    """test of callback within on_message_callback"""
    LOGGER.debug(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - message: {message.decode()}")

mqttc_sub = MQTTClient(client_id='mswa0354_sub',
                       broker_ip='10.17.105.79',
                       broker_port=8883)
mqttc_sub.subscribe(topic="paho/test/topic", callback=cb)
mqttc_sub.loop_stop()
mqttc_sub.disconnect()

mqttc_pub = MQTTClient(client_id='mswa0354_pub',
                   broker_ip='10.17.105.79',
                   broker_port=8883)
mqttc_pub.publish(topic="paho/test/topic", message='hello world')

mqttc_sub.disconnect()
mqttc_sub.connect()

mqttc_pub = MQTTClient(client_id='mswa0354_pub',
                       username='rosbrian',
                       password='foobar',
                       broker_ip='10.17.105.79',
                       broker_port=8883)

mqttc_pub.publish(topic="paho/test/topic", message='hello world')
mqttc_pub.loop_stop()
mqttc_pub.disconnect()
# ----------------------------------------------------------------------------------------------------------------------
# test connection without using any credentials
# ----------------------------------------------------------------------------------------------------------------------
import simplemqtt
client = simplemqtt.MQTTClient(client_id='test_client', broker_ip='192.168.1.103', broker_port=1883)
# ----------------------------------------------------------------------------------------------------------------------
# test connection without using any credentials
# ----------------------------------------------------------------------------------------------------------------------
import simplemqtt
simplemqtt.enable_logging()
client_pwd = simplemqtt.MQTTClient(client_id='test_client', broker_ip='192.168.1.103', broker_port=1883,
                              username='foobar', password='bar')
client_pwd.disconnect()

# ----------------------------------------------------------------------------------------------------------------------
# try TLS authentication and encryption
# ----------------------------------------------------------------------------------------------------------------------
import simplemqtt
from datetime import datetime as dt
simplemqtt.enable_logging()
pub = simplemqtt.MQTTClient(broker_ip='192.168.1.103', broker_port=8883)
pub.publish(topic='pub', message='from pub')
pub.loop_stop()
pub.disconnect()

pub2 = simplemqtt.MQTTClient(broker_ip='192.168.1.103', broker_port=8883)
pub2.publish(topic='pub', message='from pub2')
pub2.disconnect()

def on_message(client, userdata, message):
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - topic: {message.topic}, payload: {message.payload.decode()}")
    
sub = simplemqtt.MQTTClient(broker_ip='192.168.1.103', broker_port=8883)
sub.subscribe(topic='pub', callback=on_message)
sub.loop_stop()
sub.disconnect()

sub2 = simplemqtt.MQTTClient(broker_ip='192.168.1.103', broker_port=8883)
sub2.subscribe(topic='pub', callback=on_message)
sub2.loop_stop()
sub2.disconnect()
# ----------------------------------------------------------------------------------------------------------------------
# try TLS with paho
# ----------------------------------------------------------------------------------------------------------------------
import paho.mqtt.client as mqtt
# when `use_identity_as_username true` is in the .conf, you don't need to supply a client_id
paho_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# client.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/chain.crt")
# I've found that a client can connect without any credentials, but can't do anything.  Maybe try adding
# 'allow_anonymous true' in the 8883 block of the .conf.
paho_client.tls_set(ca_certs="/home/rosbrian/PycharmProjects/wood_furnace_local/simplemqtt/mosquitto/certs/chain.crt",
             certfile="/home/rosbrian/PycharmProjects/wood_furnace_local/simplemqtt/mosquitto/certs/client.crt",
             keyfile="/home/rosbrian/PycharmProjects/wood_furnace_local/simplemqtt/mosquitto/certs/client.key",
             tls_version = 2)
paho_client.connect(host='192.168.1.103', port=8883)
paho_client.disconnect()
# ----------------------------------------------------------------------------------------------------------------------
# pub and sub with the same object...works
# ----------------------------------------------------------------------------------------------------------------------
import simplemqtt
from datetime import datetime as dt

simplemqtt.enable_logging()
client = simplemqtt.MQTTClient(broker_ip='192.168.1.103',
                               broker_port=8883,
                               cert_chain='/home/rosbrian/PycharmProjects/wood_furnace_local/simplemqtt/mosquitto/scripts/client_certs/chain.crt',
                               cert='/home/rosbrian/PycharmProjects/wood_furnace_local/simplemqtt/mosquitto/scripts/client_certs/client.crt',
                               key='/home/rosbrian/PycharmProjects/wood_furnace_local/simplemqtt/mosquitto/scripts/client_certs/client.key')
pw_client = simplemqtt.MQTTClient(broker_ip='192.168.1.103',
                               broker_port=1883,
                               username='foo',
                               password='foobar',
                               client_id='test_client')

client.publish(topic='test/pub', message='from pub')
client.loop_stop()
client.disconnect()

def on_message(client, userdata, message):
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - topic: {message.topic}, payload: {message.payload.decode()}")

pw_client.subscribe(topic='test/#', callback=on_message)
pw_client.disconnect()

# ----------------------------------------------------------------------------------------------------------------------
# keep last n seconds of temps in a deque
# ----------------------------------------------------------------------------------------------------------------------
from collections import deque
import simplemqtt
from datetime import datetime as dt

simplemqtt.enable_logging()
temp_samples = deque(maxlen=10)
pw_client = simplemqtt.MQTTClient(broker_ip='192.168.1.103',
                                  broker_port=1883,
                                  username='foo',
                                  password='foobar',
                                  client_id='test_client')
def on_message(client, userdata, message):
    global temp_samples
    temp_samples.append(float(message.payload.decode()))

pw_client.subscribe(topic='temp', callback=on_message)

def get_temp(shared_object: deque):
    """Get the average value."""
    avg = sum(shared_object) / len(shared_object)
    print(f"average F: {avg}")

get_temp(temp_samples)
pw_client.disconnect()


