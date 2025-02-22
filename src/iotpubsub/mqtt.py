"""This module uses paho.mqtt.client.CallbackAPIVersion.VERSION2, which is needed when using MQTTv5 (v5.0).  None of
the capabilities of MQTTv5 are needed (only those of MQTTv31 (v3.1)), however, the official documentation uses
CallbackAPIVersion.VERSION2, which was used to develop the code in this module.  Many examples online use
CallbackAPIVersion.VERSION1, which means that they won't have the *reason_code* and *properties* parameters in callback
functions since these are only mandatory for MQTTv5 callbacks.  When used in callbacks but only using MQTTv31,
these parameter's arguments will always be None."""

import pyutils
from random import randint
import paho.mqtt.client as mqtt
from logging import getLogger
from socket import timeout, gethostname
import ssl
pyutils.logging_to_console()

LOGGER = getLogger(__name__)


class MQTTClient(pyutils.ArgCheck, mqtt.Client):
    """Connect to a MQTT broker and publish to multiple topics along with subscribing to multiple topics
    simultaneously."""
    def __init__(self,
                 broker_ip: str,
                 broker_port: int,
                 username: str = None,
                 password: str = None,
                 client_id: str = None):
        """
        :param username: username known by the broker
        :param client_id: distinct string on the broker

        Examples:
            Typical use:
                >>> import pyutils
                >>> client = pyutils.MTQQClient(username='<username>', password='<password>', client_id='<client id>')
            Publish a message:
                >>> client.publish(topic='<topic>', message='<message>', qos=0, retain=False)
            Subscribe to a topic:
                >>> def foo():
                >>>  # do stuff when message is received
                >>> client.subscribe(topic='<topic>', callback=foo, qos=0)
        """
        if client_id is None:
            client_id = f"{gethostname()}-{randint(0,100)}"
        kwargs = dict(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        super(MQTTClient, self).__init__(subclass_name= self.__class__.__name__, **kwargs)
        self.logger = pyutils.ClassNameAttribute(logger=LOGGER, class_name=self.__class__.__name__)
        self.client_id = client_id
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        if username is not None and password is not None:
            self._username = username
            self._password = password
#        else:
#            # config TLS
#
#                           certfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.crt",
#                           keyfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/client.key",
#                           tls_version=ssl.PROTOCOL_TLSv1_2)
#        self.tls_set(ca_certs="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/ca-root.crt",
#                     certfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/4711.crt",
#                     keyfile="/Volumes/Shared3/Surg-MAG/users/rosbrian/mosq/4711.key",
#                     tls_version=ssl.PROTOCOL_TLSv1_2)
#
#        self.tls_insecure_set(False)  # Ensure this is False for security

        # self.username_pw_set(self.username, self.__login_password)
        self.logger.debug("sending CONNECT")
        try:
            self.connect()
        except timeout:
            LOGGER.exception("failed to connect to broker.  is VPN active?  otherwise, see the broker's logs")
        except ConnectionRefusedError:
            LOGGER.exception("looks like is the broker is down")

        self.on_connect = self.on_connect_callback
        self.on_publish = self.on_publish_callback
        self.on_subscribe = self.on_subscribe_callback
        self.on_message = self.on_message_callback
        self.on_log = self.on_log_callback
        self.on_disconnect = self.on_disconnect_callback
        self.is_publisher = False
        self.is_subscriber = False
        self.publish_topics = set()
        self._userdata = {'publish': {'current topic': '', 'message id': 0}, 'subscribe': {'last subscribed topic': ''}}

    def connect(self):
        """Allow re-establishment of a connection that's been disconnected by using self.connect() rather than having
        to suppy the ip address and port."""
        super().connect(self.broker_ip, self.broker_port)
        # Start a loop in a new thread to listen for the CONNACK.   By default, the broker will send a PINGREQ to the
        # client every 60 seconds.  This loop will take care of sending back a PINGRESP to keep the connection alive.
        # A call to Client.disconnect() stops the loop.
        self.loop_start()

    def on_connect_callback(self, client, userdata, flags, reason_code, properties):
        """Callback for receiving a CONNACK packet after attempting to connect to a broker."""
        if not reason_code.is_failure:
            self.logger.info("connected to broker")
        else:
            self.logger.error(f"failed to connect to broker, CONNACK packet return code: {reason_code}")
            # see https://docs.emqx.com/en/cloud/latest/connect_to_deployments/mqtt_client_error_codes.html#connack-packet
            # for error codes.

    def on_publish_callback(self,client, userdata, mid, reason_code, properties):
        if mid == self._userdata['publish']['message id']:
            self.logger.debug(f"received PUBACK for message id {mid}, likely for topic "
                              f"'{self._userdata['publish']['current topic']}'")
        else:
            self.logger.debug(f"received PUBACK for message id {mid}, however, it doesn't correspond to the last "
                              f"topic that was published to")

    def on_message_callback(self, client, userdata, message):
        """Use the callback that corresponds to the topic that the message was received for."""
        callback_for_topic = self._userdata['subscribe'][message.topic]['callback']
        self.logger.debug(f"received message '{message.payload.decode()}' for topic '{message.topic}' and supplying "
                          f"the message as an argument to the '{callback_for_topic.__name__}' callback")
        callback_for_topic(message.payload)

    def on_subscribe_callback(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry.
        last_subscribed_topic = self._userdata['subscribe']['last subscribed topic']
        if reason_code_list[0].is_failure:
            self.logger.error(f"broker rejected subscription to '{last_subscribed_topic}' reason code: "
                              f"{reason_code_list[0]}")
        else:
            self.logger.debug(f"broker granted subscription to '{last_subscribed_topic}'")
            if self._userdata['subscribe'][last_subscribed_topic]['callback'] is None:
                self.logger.debug("no callback function was provided, therefore, no action will be taken upon "
                                  "receiving messages")

    def on_disconnect_callback(self, client, userdata, disconnect_flags, reason_code, properties):
        """Clear attributes in preparation for a subsequent reconnection."""
        self.logger.debug(f"disconnected from broker")
        self.is_publisher = False
        self.is_subscriber = False

    def on_log_callback(self, client, userdata, paho_log_level, messages):
        """Receive log events output by the server.  Basically, get the server's log."""
        # It looks like only the log events pertaining to the client are received.
        self.logger.debug(f"messages: {messages}")

    def publish(self, topic: str, message: str, qos: int = 0, retain: bool = False):
        """
        :param message: message must be a string, bytearray, int, float or None
        """
        # self._userdata is provided to all callbacks as the argument to their userdata parameter.  self._userdata \
        # may be any type.  self.user_data_set() simply assigns self._userdata.  In the callbacks, you could use
        # self._userdata rather than using the argument to the userdata parameter.  I've proven that the argument
        # points to self._userdata by mutating the argument and having the change reflected in self._userdata.
        # I'm assigning a dict to self._userdata, which will be accessed in self.on_publish_callback().  The dict \
        # needs


        msg_info = super().publish(topic=topic, payload=message, qos=qos, retain=retain)
        self.logger.debug(f"sent message id {msg_info.mid} to broker")
        self.publish_topics.add(topic)
        self._userdata['publish']['current topic'] = topic
        self._userdata['publish']['message id'] = msg_info.mid
        # wait_for_publish() will block until there's a PUBACK received.
        try:
            msg_info.wait_for_publish()
        except RuntimeError:
            self.logger.exception("client not connected to broker")

    def subscribe(self, topic: str, callback, qos = 0):
        """This is my own implementation ofpaho.mqtt.subscribe.callback.  Provide a callback to take place of
        self.on_message_callback."""
        assert callable(callback) is True, 'call needs to be a function'
        self._userdata['subscribe'][topic] = {'callback': callback,
                                               'docstring': callback.__doc__,
                                               'qos': qos}
        self._userdata['subscribe']['last subscribed topic'] = topic
        super().subscribe(topic=topic, qos=qos)

def cb(message):
    """test of callback within on_message_callback"""
    LOGGER.debug('cb() called')

mqttc_sub = MQTTClient(client_id='mswa0354_sub',
                       username='rosbrian',
                       password='foobar',
                       broker_ip='192.168.1.100',
                       broker_port=1883)
mqttc_sub.subscribe(topic="paho/test/topic", callback=cb)

mqttc_pub = MQTTClient(client_id='mswa0354_pub',
                   username='rosbrian',
                   password='foobar',
                   broker_ip='192.168.1.100',
                   broker_port=1883)
mqttc_pub.publish(topic="paho/test/topic", message='hello world')

mqttc_sub.disconnect()
mqttc_sub.connect()

mqttc_pub = MQTTClient(client_id='mswa0354_pub',
                       username='rosbrian',
                       password='foobar',
                       broker_ip='10.17.105.79',
                       broker_port=8883)

mqttc_pub.publish(topic="paho/test/topic", message='hello world')

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
sub.connect(host='10.17.105.79', port=8883)
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
from pydb import logging_to_console
from datetime import datetime as dt
logging_to_console()

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
