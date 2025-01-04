#!/usr/bin/python3
"""Sengled Bulb Integration."""
import json
import logging
import time
from urllib.parse import urlparse
from uuid import uuid4

import paho.mqtt.client as mqtt
import requests

from .devices.bulbs.bulb import Bulb
from .devices.bulbs.bulbproperty import BulbProperty
from .devices.exceptions import SengledApiAccessToken
from .devices.request import Request
from .devices.switch import Switch

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
        _LOGGER.info("Sengled Api initializing.")
        SESSION.username = user_name
        SESSION.password = password
        SESSION.countryCode = country
        SESSION.wifi = wifi

    async def async_init(self):
        _LOGGER.info("Sengled Api initializing async.")
        self._access_token = await self.async_login(
            SESSION.username, SESSION.password, SESSION.device_id
        )

    async def async_login(self, username, password, device_id):
        """
        Log user into server.
        Returns True on success, False on failure.
        """
        _LOGGER.info("Sengledapi: Login")

        if SESSION.jsession_id:
            if not await self.async_is_session_timeout():
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
                self.initialize_mqtt()
            else:
                self.reinitialize_mqtt()

        return True

    def is_valid_login(self):
        if SESSION.jsession_id is None:
            return False
        return True

    async def async_is_session_timeout(self):
        """
        Determine whether or not the session has timed out.
        Returns True if timed out, False otherwise.
        """
        _LOGGER.info("SengledApi: Session Timeout")

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
        _LOGGER.debug("SengledApi: Parse MQTT Server Info" + str(url))

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
            for devices in data["deviceList"]:
                found = False

                for dev in SESSION.wifi_devices:
                    if dev.uuid == devices["deviceUuid"]:
                        found = True
                        break
                if not found:
                    _LOGGER.debug("SengledApi: Get Wifi Mqtt Devices %s", devices)
                    SESSION.wifi_devices.append(BulbProperty(self, devices, True))
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
        _LOGGER.info("SengledApi: List All Bulbs.")
        bulbs = []
        for device in await self.async_get_devices():
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
                    False,
                )
            )
        if SESSION.wifi:
            for device in await self.async_get_wifi_devices():
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
                        True,
                    )
                )
        return bulbs

    async def async_list_switch(self):
        _LOGGER.info("Sengled Api listing switches.")
        switch = []
        for device in await self.async_get_devices():
            _LOGGER.debug(device)
            if "lampInfos" in device:
                for switch in device["lampInfos"]:
                    if switch["attributes"]["productCode"] == "E1E-G7F":
                        switch.append(
                            Switch(
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

    async def async_do_request(self, url, payload, jsessionId):
        try:
            return await Request(url, payload).async_get_response(jsessionId)
        except Exception as e:
            _LOGGER.error("Error in async_do_request: %s", e)
            raise

    async def async_do_login_request(self, url, payload):
        _LOGGER.info("SengledApi: Login Request.")
        try:
            return await Request(url, payload).async_get_login_response()
        except Exception as e:
            _LOGGER.error("Error in async_do_login_request: %s", e)
            return Request(url, payload).get_login_response()

    async def async_do_is_session_timeout_request(self, url, payload):
        _LOGGER.info("SengledApi: Sengled Api doing request.")
        try:
            return await Request(url, payload).async_is_session_timeout_response(
                SESSION.jsession_id
            )
        except Exception as e:
            _LOGGER.error("Error in async_do_is_session_timeout_request: %s", e)
            return Request(url, payload).is_session_timeout_response(
                SESSION.jsession_id
            )

    def initialize_mqtt(self):
        _LOGGER.info("SengledApi: Initialize the MQTT connection")
        if not SESSION.jsession_id:
            return False

        def on_message(api, userdata, msg):
            if msg.topic in SESSION.subscribe:
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
        _LOGGER.info("SengledApi: Start mqtt loop")
        return True

    def reinitialize_mqtt(self):
        _LOGGER.info("SengledApi: Re-initialize the MQTT connection")
        if SESSION.mqtt_client is None or not SESSION.jsession_id:
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
            self.subscribe_mqtt(topic, SESSION.subscribe[topic])

        return True

    def publish_mqtt(self, topic, payload=None):
        _LOGGER.info("SengledApi: Publish MQTT message")
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
        _LOGGER.info("SengledApi: Subscribe to an MQTT Topic")
        if SESSION.mqtt_client is None:
            return False

        r = SESSION.mqtt_client.subscribe(topic)
        _LOGGER.info("SengledApi: Subscribe Mqtt %s", str(r))
        if r[0] != mqtt.MQTT_ERR_SUCCESS:
            return False

        SESSION.subscribe[topic] = callback
        return True

    def unsubscribe_mqtt(self, topic, callback):
        _LOGGER.info("SengledApi: Unsubscribe from an MQTT topic")
        if topic in SESSION.subscribe:
            del SESSION.subscribe[topic]
