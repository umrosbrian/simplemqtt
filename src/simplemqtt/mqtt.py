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
from .utils import ClassNameAttribute
import ssl

LOGGER = getLogger(__name__)


class MQTTClient(mqtt.Client):
    """Connect to a MQTT broker and publish to multiple topics along with subscribing to multiple topics
    simultaneously."""
    def __init__(self,
                 broker_ip: str,
                 broker_port: int,
                 cert_chain: str = None,
                 cert: str = None,
                 key: str = None,
                 username: str = None,
                 password: str = None,
                 client_id: str = None):
        """When using certificate-based authentication, the *cert_chain*, *cert* and *key* parameters all need an
        argument and arguments for the *username* and *password* parameters will be ignored.  The opposite is true
        when using password-based authenication.
        :param username: username known to the broker
        :param password: username's password
        :param client_id: Distinct string on the broker.  Only used with password-based authentication.  When an
        argument isn't provided, a random string will be used.

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
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.cert_chain = cert_chain
        self.cert = cert
        self.key = key
        self.client_id = client_id

        # The base class already has a 'logger' attribute.
        self.cls_logger = ClassNameAttribute(logger=LOGGER, class_name=self.__class__.__name__)

        # Do a check of the authentication arguments first.
        if self.cert_chain is not None and self.cert is not None and self.key is not None:
            # The client id is in the file assigned to self.cert so we don't need to provide it to the client_id /
            # parameter
            super(MQTTClient, self).__init__(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            self.tls_set(ca_certs=self.cert_chain,
                         certfile=self.cert,
                         keyfile=self.key,
                         tls_version=2)  # for version 1.2
            # Ensure this is False for security.  Shouldn't be needed but here for redundancy.
            self.tls_insecure_set(False)
            self.cls_logger.debug("base class configured to use certificate-based authentication and encryption")
        if username is not None and password is not None:
            if self.client_id is None:
                self.client_id = f"{gethostname()}-{randint(0,100)}"
            super(MQTTClient, self).__init__(client_id=self.client_id,
                                             callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            self.username_pw_set(username, password)
            self.cls_logger.debug(f"base class configured to use password-based authentication using "
                              f"client_id '{self.client_id}'")

        super().enable_logger(logger=self.cls_logger)  # get logging messages from base class
        self.cls_logger.debug("sending CONNECT")
        try:
            self.connect()
        except timeout:
            LOGGER.exception("failed to connect to broker.  is VPN active?  otherwise, see the broker's logs")
        except ConnectionRefusedError:
            LOGGER.exception("looks like is the broker is down")

        # Overriding the base class methods (on the left) with more verbose method names (on the right).
        self.on_connect = self.on_connect_callback
        self.on_publish = self.on_publish_callback
        self.on_subscribe = self.on_subscribe_callback
        self.on_message = self.on_message_callback
        self.on_log = self.on_log_callback
        self.on_disconnect = self.on_disconnect_callback
        self.is_publisher = False
        self.is_subscriber = False
        self.publish_topics = set()
        self.userdata = {'publish': {'current topic': '', 'message id': 0}, 'subscribe': {'last subscribed topic': ''}}

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
            self.cls_logger.info("connected to broker")
        else:
            self.cls_logger.error(f"failed to connect to broker, CONNACK packet return code: {reason_code}")
            # see https://docs.emqx.com/en/cloud/latest/connect_to_deployments/mqtt_client_error_codes.html#connack-packet
            # for error codes.

    def on_publish_callback(self,client, userdata, mid, reason_code, properties):
        if mid == self.userdata['publish']['message id']:
            self.cls_logger.debug(f"received PUBACK for message id {mid}, likely for topic "
                              f"'{self.userdata['publish']['current topic']}'")
        else:
            self.cls_logger.debug(f"received PUBACK for message id {mid}, however, it doesn't correspond to the last "
                              f"topic that was published to")

    def on_message_callback(self, client, userdata, message):
        """Use the callback that corresponds to the topic that the message was received for."""
        callback_for_topic = self.userdata['subscribe'][message.topic]['callback']
        self.cls_logger.debug(f"received message '{message.payload.decode()}' for topic '{message.topic}' and supplying "
                          f"the message as an argument to the '{callback_for_topic.__name__}' callback")
        callback_for_topic(message.payload)

    def on_subscribe_callback(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry.
        last_subscribed_topic = self.userdata['subscribe']['last subscribed topic']
        if reason_code_list[0].is_failure:
            self.cls_logger.error(f"broker rejected subscription to '{last_subscribed_topic}' reason code: "
                              f"{reason_code_list[0]}")
        else:
            self.cls_logger.debug(f"broker granted subscription to '{last_subscribed_topic}'")
            if self.userdata['subscribe'][last_subscribed_topic]['callback'] is None:
                self.cls_logger.debug("no callback function was provided, therefore, no action will be taken upon "
                                  "receiving messages")

    def on_disconnect_callback(self, client, userdata, disconnect_flags, reason_code, properties):
        """Clear attributes in preparation for a subsequent reconnection."""
        self.cls_logger.debug(f"disconnected from broker")
        self.is_publisher = False
        self.is_subscriber = False

    def on_log_callback(self, client, userdata, paho_log_level, messages):
        """Receive log events output by the server.  Basically, get the server's log."""
        # It looks like only the log events pertaining to the client are received.
        self.cls_logger.debug(f"messages: {messages}")

    def publish(self, topic: str, message: str, qos: int = 0, retain: bool = False):
        """
        :param message: message must be a string, bytearray, int, float or None
        """
        # self.userdata is provided to all callbacks as the argument to their userdata parameter.  self.userdata \
        # may be any type.  self.user_data_set() simply assigns self.userdata.  In the callbacks, you could use
        # self.userdata rather than using the argument to the userdata parameter.  I've proven that the argument
        # points to self.userdata by mutating the argument and having the change reflected in self.userdata.
        # I'm assigning a dict to self.userdata, which will be accessed in self.on_publish_callback().  The dict \
        # needs


        msg_info = super().publish(topic=topic, payload=message, qos=qos, retain=retain)
        self.cls_logger.debug(f"sent message id {msg_info.mid} to broker")
        self.publish_topics.add(topic)
        self.userdata['publish']['current topic'] = topic
        self.userdata['publish']['message id'] = msg_info.mid
        # wait_for_publish() will block until there's a PUBACK received.
        try:
            msg_info.wait_for_publish()
        except RuntimeError:
            self.cls_logger.exception("client not connected to broker")

    def subscribe(self, topic: str, callback, qos = 0):
        """This is my own implementation of paho.mqtt.subscribe.callback.  Provide a callback to take place of
        self.on_message_callback."""
        assert callable(callback) is True, 'call needs to be a function'
        self.on_message = callback
        self.userdata['subscribe'][topic] = {'callback': callback,
                                             'docstring': callback.__doc__,
                                             'qos': qos}
        self.userdata['subscribe']['last subscribed topic'] = topic
        super().subscribe(topic=topic, qos=qos)

