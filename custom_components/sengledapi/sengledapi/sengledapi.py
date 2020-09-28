#!/usr/bin/python3
"""Sengled Bulb Integration."""
# from .devices.sengled_wifi_bulb_property import SengledWifiBulbProperty
from .devices.bulbs.bulbproperty import BulbProperty
from .devices.request import Request

from .devices.bulbs.bulb import Bulb
from .devices.bulbs.wifi_bulb import WifiBulb

from .devices.switch import Switch

from .devices.exceptions import SengledApiAccessToken

import logging

from urllib.parse import urlparse
from uuid import uuid4
import paho.mqtt.client as mqtt
import requests
import time
import json

_LOGGER = logging.getLogger(__name__)


class SengledSession:

    username = ""
    password = ""
    countryCode = ""
    wifi = False
    device_id = uuid4().hex[:-16]
    jsession_id = ""
    mqtt_server = {
        "host": "us-mqtt.cloud.sengled.com",
        "port": 443,
        "path": "/mqtt",
    }
    mqtt_client = None
    subscribe = {}
    devices = []
    wifi_devices = []


SESSION = SengledSession()


class SengledApi:
    def __init__(self, user_name, password, country, wifi):
        _LOGGER.debug("Sengled Api initializing.")
        SESSION.username = user_name
        SESSION.password = password
        SESSION.countryCode = country
        SESSION.wifi = wifi

    async def async_init(self):
        _LOGGER.debug("Sengled Api initializing async.")
        self._access_token = await self.async_login(
            SESSION.username, SESSION.password, SESSION.device_id
        )

    async def async_login(self, username, password, device_id):
        """
        Log user into server.
        Returns True on success, False on failure.
        """
        _LOGGER.debug("Sengledapi: async_login")

        if SESSION.jsession_id:
            if not self.async_is_session_timeout():
                return

        url = "https://ucenter.cloud.sengled.com/user/app/customer/v2/AuthenCross.json"
        payload = {
            "uuid": SESSION.device_id,
            "user": SESSION.username,
            "pwd": SESSION.password,
            "osType": "android",
            "productCode": "life",
            "appCode": "life",
        }

        data = await self.async_do_login_request(url, payload)

        _LOGGER.debug("SengledApi Login %s", str(data))

        if "jsessionId" not in data or not data["jsessionId"]:
            return False

        SESSION.jsession_id = data["jsessionId"]

        if SESSION.wifi:
            await self.async_get_server_info()

            if not SESSION.mqtt_client:
                _LOGGER.debug(
                    "SengledApi: Login initialize mqtt client %s",
                    str(SESSION.mqtt_client),
                )
                self.initialize_mqtt()
            else:
                self.reinitialize_mqtt()

        return True

    def is_valid_login(self):
        if SESSION.jsession_id == None:
            return False
        return True

    async def async_is_session_timeout(self):
        """
        Determine whether or not the session has timed out.
        Returns True if timed out, False otherwise.
        """
        _LOGGER.debug("SengledApi: async_is_session_timeout")

        if not SESSION.jsession_id:
            return True

        url = "https://ucenter.cloud.sengled.com/user/app/customer/isSessionTimeout.json"  # noqa
        payload = {
            "uuid": SESSION.device_id,
            "os_type": "android",
            "appCode": "life",
        }

        data = await self.async_do_is_session_timeout_request(url, payload)

        _LOGGER.debug("SengledApi: async_is_session_timeout " + str(data))

        if "info" not in data or data["info"] != "OK":
            return True

        return False

    async def async_get_server_info(self):
        """Get secondary server info from the primary."""
        if not SESSION.jsession_id:
            _LOGGER.debug("SengledApi: Access token is null")
            return
        url = "https://life2.cloud.sengled.com/life2/server/getServerInfo.json"
        payload = {}

        data = await self.async_do_request(url, payload, SESSION.jsession_id)

        _LOGGER.debug("SengledApi: Get MQTT Server Info" + str(data))
        if "inceptionAddr" not in data or not data["inceptionAddr"]:
            return

        url = urlparse(data["inceptionAddr"])
        if ":" in url.netloc:
            SESSION.mqtt_server["host"] = url.netloc.split(":")[0]
            SESSION.mqtt_server["port"] = int(url.netloc.split(":")[1], 10)
            SESSION.mqtt_server["path"] = url.path
        else:
            SESSION.mqtt_server["host"] = url.netloc
            SESSION.mqtt_server["port"] = 443
            SESSION.mqtt_server["path"] = url.path
        _LOGGER.debug("SengledApi: Parese MQTT Server Info" + str(url))

    async def async_get_wifi_devices(self):
        """
        Get list of Wifi connected devices.
        """
        if not SESSION.wifi_devices:
            url = "https://life2.cloud.sengled.com/life2/device/list.json"
            payload = {}
            data = await self.async_do_request(url, payload, SESSION.jsession_id)
            if "deviceList" not in data or not data["deviceList"]:
                return SESSION.wifi_devices
            for d in data["deviceList"]:
                found = False

                for dev in SESSION.wifi_devices:
                    if dev.uuid == d["deviceUuid"]:
                        found = True
                        break
                if not found:
                    _LOGGER.debug("SengledApi: Get Wifi Mqtt Devices %s", d)
                    SESSION.wifi_devices.append(BulbProperty(self, d, True))
        return SESSION.wifi_devices

    async def async_get_devices(self):
        _LOGGER.debug("SengledApi: Get Devices.")
        if not SESSION.devices:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )
            payload = {}
            data = await self.async_do_request(url, payload, SESSION.jsession_id)
            for d in data["deviceInfos"]:
                for devices in d["lampInfos"]:
                    SESSION.devices.append(BulbProperty(self, devices, False))
        return SESSION.devices

    async def discover_devices(self):
        _LOGGER.debug("SengledApi: List All Bulbs.")
        bulbs = []
        for device in await self.async_get_devices():
            _LOGGER.debug("SengledApi: List Device return %s", device)
            bulbs.append(
                Bulb(
                    self,
                    device.uuid,
                    device.name,
                    device.switch,
                    device.typeCode,
                    device.isOnline,
                    device.support_color,
                    device.support_color_temp,
                    device.support_brightness,
                    SESSION.jsession_id,
                    SESSION.countryCode,
                )
            )
        if SESSION.wifi:
            for device in await self.async_get_wifi_devices():
                _LOGGER.debug("SengledApi: List Wifi Device return %s", device)
                if device.support_color_temp:
                    bulbs.append(
                        WifiBulb(
                            self,
                            device.uuid,
                            device.name,
                            device.switch,
                            device.typeCode,
                            device.isOnline,
                            device.support_color,
                            device.support_color_temp,
                            device.support_brightness,
                            SESSION.jsession_id,
                            SESSION.countryCode,
                        )
                    )
        return bulbs

    async def async_list_switch(self):
        _LOGGER.debug("Sengled Api listing switches.")
        switch = []
        # This is my room list
        for device in await self.async_get_devices():
            _LOGGER.debug(device)
            if "lampInfos" in device:
                for switch in device["lampInfos"]:
                    if switch["attributes"]["productCode"] == "E1E-G7F":
                        switch.append(
                            SengledSwitch(
                                self,
                                device["deviceUuid"],
                                device["attributes"]["name"],
                                ("on" if device["attributes"]["onoff"] == 1 else "off"),
                                device["attributes"]["productCode"],
                                self._access_token,
                                SESSION.countryCode,
                            )
                        )
        return switch

    #######################Do request#######################################################
    async def async_do_request(self, url, payload, jsessionId):
        try:
            return await Request(url, payload).async_get_response(jsessionId)
        except:
            return Request(url, payload).get_response(jsessionId)

    ###################################Login Request only###############################
    async def async_do_login_request(self, url, payload):
        _LOGGER.debug("async_do_login_request - Sengled Api doing request.")
        try:
            return await Request(url, payload).async_get_login_response()
        except:
            return Request(url, payload).get_login_response()

    ######################################Session Timeout#######################################
    async def async_do_is_session_timeout_request(self, url, payload):
        _LOGGER.debug("async_do_login_request - Sengled Api doing request.")
        try:
            return await Request(url, payload).async_is_session_timeout_response(
                SESSION.jsession_id
            )
        except:
            return Request(url, payload).is_session_timeout_response(
                SESSION.jsession_id
            )

    #########################MQTT#################################################
    def initialize_mqtt(self):
        _LOGGER.debug("SengledApi: Initialize the MQTT connection")
        """Initialize the MQTT connection."""
        if not SESSION.jsession_id:
            _LOGGER.debug("SengledApi: MQTT no Accesstoken")
            return False

        def on_message(client, userdata, msg):
            if msg.topic in SESSION.subscribe:
                _LOGGER.debug(str(SESSION.subscribe))
                _LOGGER.debug(str(userdata))
                _LOGGER.debug(str(SESSION.subscribe[msg.topic](msg.payload)))
                SESSION.subscribe[msg.topic](msg.payload)

        SESSION.mqtt_client = mqtt.Client(
            client_id="{}@lifeApp".format(SESSION.jsession_id), transport="websockets"
        )
        SESSION.mqtt_client.tls_set_context()
        SESSION.mqtt_client.ws_set_options(
            path=SESSION.mqtt_server["path"],
            headers={
                "Cookie": "JSESSIONID={}".format(SESSION.jsession_id),
                "X-Requested-With": "com.sengled.life2",
            },
        )
        SESSION.mqtt_client.on_message = on_message
        SESSION.mqtt_client.connect(
            SESSION.mqtt_server["host"],
            port=SESSION.mqtt_server["port"],
            keepalive=30,
        )
        SESSION.mqtt_client.loop_start()
        _LOGGER.debug("SengledApi: Start mqtt loop")
        return True

    def reinitialize_mqtt(self):
        """Re-initialize the MQTT connection."""
        _LOGGER.debug("SengledApi: Re-initialize the MQTT connection")
        if SESSION.mqtt_client is None or not SESSION.jsession_id:
            _LOGGER.debug("MQTT _reinitialize_mqtt no Accesstoken yet")
            return False

        SESSION.mqtt_client.loop_stop()
        SESSION.mqtt_client.disconnect()
        SESSION.mqtt_client.ws_set_options(
            path=SESSION.mqtt_server["path"],
            headers={
                "Cookie": "JSESSIONID={}".format(SESSION.jsession_id),
            },
        )
        SESSION.mqtt_client.reconnect()
        SESSION.mqtt_client.loop_start()

        for topic in SESSION.subscribe:
            self._subscribe_mqtt(topic, SESSION.subscribe[topic])

        return True

    def publish_mqtt(self, topic, payload=None):
        """
        Publish an MQTT message.
        topic -- topic to publish the message on
        payload -- message to send
        Returns True if publish succeeded, False if not.
        """
        _LOGGER.debug("SengledApi: Publish MQTT message")
        if SESSION.mqtt_client is None:
            return False

        r = SESSION.mqtt_client.publish(topic, payload=payload)
        _LOGGER.debug("SengledApi: Publish Mqtt %s", str(r))
        try:
            r.wait_for_publish()
            return r.is_published
        except ValueError:
            pass

        return False

    def subscribe_mqtt(self, topic, callback):
        _LOGGER.debug("SengledApi: Subscribe to an  MQTT Topic")
        """
        Subscribe to an MQTT topic.
        topic -- topic to subscribe to
        callback -- callback to call when a message comes in
        """
        if SESSION.mqtt_client is None:
            return False

        r = SESSION.mqtt_client.subscribe(topic)
        _LOGGER.debug("SengledApi: Subscribe Mqtt %s", str(r))
        if r[0] != mqtt.MQTT_ERR_SUCCESS:
            return False

        SESSION.subscribe[topic] = callback
        return True

    def unsubscribe_mqtt(self, topic, callback):
        _LOGGER.debug("SengledApi: Unsubscribe from an MQTT topic")
        """
        Unsubscribe from an MQTT topic.
        topic -- topic to unsubscribe from
        callback -- callback from previous subscription
        """
        if topic in SESSION.subscribe:
            del SESSION.subscribe[topic]
