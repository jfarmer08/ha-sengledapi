"""Sengled Bulb Integration."""

import logging

from urllib.parse import urlparse
from uuid import uuid4
import json
import paho.mqtt.client as mqtt
import requests
import time

_LOGGER = logging.getLogger(__name__)


class SengledMqtt:
    def __init__(self, user_name, password, country, wifi):
        _LOGGER.debug("SengledApi: MQTT")
        self._jsession_id = None
        self._wifi = wifi  # Boolen Tells me to check for wifi bulbs from Sengled
        # Create device array
        self._all_devices = []
        self._all_wifi_devices = []
        self._mqtt_server = {
            "host": "us-mqtt.cloud.sengled.com",
            "port": 443,
            "path": "/mqtt",
        }
        self._mqtt_client = None
        self._devices = []
        self._subscribed = {}

    #########################MQTT#################################################
    def _get_server_info(self):
        """Get secondary server info from the primary."""
        if not self._jsession_id:
            _LOGGER.debug("Access token is null")
            return

        r = requests.post(
            "https://life2.cloud.sengled.com/life2/server/getServerInfo.json",
            headers={
                "Content-Type": "application/json",
                "Cookie": "JSESSIONID={}".format(self._jsession_id),
                "sid": self._jsession_id,
                "X-Requested-With": "com.sengled.life2",
            },
            json={},
        )

        if r.status_code != 200:
            return

        data = r.json()
        _LOGGER.debug("SengledWifi Get Server Info" + str(data))
        if "inceptionAddr" not in data or not data["inceptionAddr"]:
            return

        url = urlparse(data["inceptionAddr"])
        if ":" in url.netloc:
            self._mqtt_server["host"] = url.netloc.split(":")[0]
            self._mqtt_server["port"] = int(url.netloc.split(":")[1], 10)
            self._mqtt_server["path"] = url.path
        else:
            self._mqtt_server["host"] = url.netloc
            self._mqtt_server["port"] = 443
            self._mqtt_server["path"] = url.path
        _LOGGER.debug("Sengled Wifi get server info" + str(url))

    def _initialize_mqtt(self):
        _LOGGER.debug("Sengledwifi Initialize the MQTT connection")
        """Initialize the MQTT connection."""
        if not self._jsession_id:
            _LOGGER.debug("MQTT _initialize_mqtt no Accesstoken yet")
            return False

        def on_message(client, userdata, msg):
            if msg.topic in self._subscribed:
                self._subscribed[msg.topic](msg.payload)

        self._mqtt_client = mqtt.Client(
            client_id="{}@lifeApp".format(self._jsession_id), transport="websockets"
        )
        self._mqtt_client.tls_set_context()
        self._mqtt_client.ws_set_options(
            path=self._mqtt_server["path"],
            headers={
                "Cookie": "JSESSIONID={}".format(self._jsession_id),
                "X-Requested-With": "com.sengled.life2",
            },
        )
        self._mqtt_client.on_message = on_message
        self._mqtt_client.connect(
            self._mqtt_server["host"], port=self._mqtt_server["port"], keepalive=30,
        )
        self._mqtt_client.loop_start()

        return True

    def _reinitialize_mqtt(self):
        """Re-initialize the MQTT connection."""
        _LOGGER.debug("Sengledwifi Re-initialize the MQTT connection")
        if self._mqtt_client is None or not self._jsession_id:
            _LOGGER.debug("MQTT _reinitialize_mqtt no Accesstoken yet")
            return False

        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()
        self._mqtt_client.ws_set_options(
            path=self._mqtt_server["path"],
            headers={"Cookie": "JSESSIONID={}".format(self._jsession_id),},
        )
        self._mqtt_client.reconnect()
        self._mqtt_client.loop_start()

        for topic in self._subscribed:
            self._subscribe_mqtt(topic, self._subscribed[topic])

        return True

    def _publish_mqtt(self, topic, payload=None):
        """
        Publish an MQTT message.
        topic -- topic to publish the message on
        payload -- message to send
        Returns True if publish succeeded, False if not.
        """
        _LOGGER.debug("Sengledwifi Publish MQTT message")
        if self._mqtt_client is None:
            return False

        r = self._mqtt_client.publish(topic, payload=payload)

        try:
            r.wait_for_publish()
            return r.is_published
        except ValueError:
            pass

        return False

    def _subscribe_mqtt(self, topic, callback):
        _LOGGER.debug("Sengledwifi Subscribe to an  MQTT Topic")
        """
        Subscribe to an MQTT topic.
        topic -- topic to subscribe to
        callback -- callback to call when a message comes in
        """
        if self._mqtt_client is None:
            return False

        r = self._mqtt_client.subscribe(topic)
        if r[0] != mqtt.MQTT_ERR_SUCCESS:
            return False

        self._subscribed[topic] = callback
        return True

    def _unsubscribe_mqtt(self, topic, callback):
        _LOGGER.debug("Sengledwifi Unsubscribe from an MQTT topic")
        """
        Unsubscribe from an MQTT topic.
        topic -- topic to unsubscribe from
        callback -- callback from previous subscription
        """
        if topic in self._subscribed:
            del self._subscribed[topic]
