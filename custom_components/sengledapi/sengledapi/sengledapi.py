#!/usr/bin/python3
"""Sengled Bulb Integration."""
from .sengled_wifi_bulb_property import SengledWifiBulbProperty
from .sengled_request import SengledRequest

from .bulbs.sengled_bulb import SengledBulb
from .bulbs.sengled_bulb_flood_motion import SengledBulbFloodMotion
from .bulbs.sengled_color_bulb import SengledColorBulb
from .sengled_wifi_bulb import SengledWifiBulb
from .sengled_wifi_color_bulb import SengledWifiColorBulb

from .sengled_switch import SengledSwitch

from .sengledapi_exceptions import SengledApiAccessToken

import logging

from urllib.parse import urlparse
from uuid import uuid4
import paho.mqtt.client as mqtt
import requests
import time
import json

_LOGGER = logging.getLogger(__name__)


class SengledApi:
    def __init__(self, user_name, password, country, wifi):
        _LOGGER.debug("Sengled Api initializing.")
        self._user_name = user_name
        self._password = password
        self._device_id = uuid4().hex[:-16]
        self._in_error_state = False
        self._country = country
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

    async def async_init(self):
        _LOGGER.debug("Sengled Api initializing async.")
        self._access_token = await self.async_login(
            self._user_name, self._password, self._device_id
        )

    async def async_login(self, username, password, device_id):
        """
        Log user into server.
        Returns True on success, False on failure.
        """
        _LOGGER.debug("Sengledapi: async_login")

        if self._jsession_id:
            if not self._is_session_timeout():
                return

        url = "https://ucenter.cloud.sengled.com/user/app/customer/v2/AuthenCross.json"
        payload = {
            "uuid": self._device_id,
            "user": self._user_name,
            "pwd": self._password,
            "osType": "android",
            "productCode": "life",
            "appCode": "life",
        }

        data = await self.async_do_login_request(url, payload)

        _LOGGER.debug("SengledApi Login %s", str(data))

        if "jsessionId" not in data or not data["jsessionId"]:
            return False

        self._jsession_id = data["jsessionId"]

        if self._wifi:
            self._get_server_info()

            if not self._mqtt_client:
                _LOGGER.debug(
                    "SengledApi: Login initialize mqtt client %s",
                    str(self._mqtt_client),
                )
                self._initialize_mqtt()
            else:
                self._reinitialize_mqtt()
            # no need to get devices here lets wait until HA tells me too
            # self.get_devices(force_update=True)

        return True

    def is_valid_login(self):
        if self._jsession_id == None:
            return False
        return True

    async def _is_session_timeout(self):
        """
        Determine whether or not the session has timed out.
        Returns True if timed out, False otherwise.
        """
        _LOGGER.debug("SengledAPI _is_session_timeout")

        if not self._jsession_id:
            return True

        url = "https://ucenter.cloud.sengled.com/user/app/customer/isSessionTimeout.json"  # noqa
        payload = {
            "uuid": self._device_id,
            "os_type": "android",
            "appCode": "life",
        }

        data = await self.async_do_is_session_timeout_request(url, payload)

        _LOGGER.debug("Sengledapi: _is_session_timeout " + str(data))

        if "info" not in data or data["info"] != "OK":
            return True

        return False

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

    async def get_devices(self, force_update=False):
        """
        Get list of connected devices.
        force_update -- whether or not to force an update from the server
        """
        if not self._all_wifi_devices:
            url = "https://life2.cloud.sengled.com/life2/device/list.json"
            payload = {}
            data = await self.async_do_request(url, payload, self._jsession_id)
            if "deviceList" not in data or not data["deviceList"]:
                return self._all_wifi_devices
            for d in data["deviceList"]:
                found = False

                for dev in self._all_wifi_devices:
                    if dev.uuid == d["deviceUuid"]:
                        found = True
                        break
                if not found:
                    # _LOGGER.debug("get devices %s", d)
                    self._all_wifi_devices.append(SengledWifiBulbProperty(self, d))
        return self._all_wifi_devices

    async def async_get_devices(self):
        _LOGGER.debug("Sengled Api getting devices.")
        if not self._all_devices:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )
            payload = {}
            data = await self.async_do_request(url, payload, self._jsession_id)
            self._all_devices = data["deviceInfos"]
        return self._all_devices

    async def async_list_bulbs(self):
        _LOGGER.debug("Sengled Api listing bulbs.")
        bulbs = []
        # This is my room list
        for device in await self.async_get_devices():
            _LOGGER.debug(device)
            if "lampInfos" in device:
                for light in device["lampInfos"]:
                    if (
                        light["attributes"]["productCode"] == "E11-G13"
                    ):  # Sengled Soft White A19 Bulb
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-G14"
                    ):  # Sengled Daylight A19 Bulb
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-G33"
                    ):  # Sengled Element Classic A60 B22
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E12-N14"
                    ):  # Sengled Soft White BR30 Bulb
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-G23"
                    ):  # Sengled Element Classic A60 E27
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E1A-AC2"
                    ):  # Sengled Element Downlight
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E13-N11"
                    ):  # Sengled Motion Sensor PAR38 Bulb
                        bulbs.append(
                            SengledBulbFloodMotion(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "Z01-CIA19NAE26"
                    ):  # Sengled Element Touch A19 E26
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "Z01-A60EAE27"
                    ):  # Sengled Element Plus A60 E27
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "Z01-A19NAE26"
                    ):  # Sengled Element Plus A19 Bulb
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-N13"
                    ):  # Sengled Element Extra Bright Soft White A19 Bulb
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-N14"
                    ):  # Sengled Element Extra Bright Daylight A19 Bulb
                        bulbs.append(
                            SengledBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-N1EA"
                    ):  # Sengled Multicolor A19 Bulb. This is a Multicolor Bulb. We cannot control the color temp.
                        bulbs.append(
                            SengledColorBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E12-N1E"
                    ):  # Sengled Soft White BR30 Bulb. This is a Multicolor Bulb. We cannot control the color temp.
                        bulbs.append(
                            SengledColorBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E1G-G8E"
                    ):  # Sengled Multicolor Light Strip 2M. This is a Multicolor Bulb. We cannot control the color temp.
                        bulbs.append(
                            SengledColorBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-U2E"
                    ):  # Sengled Element Color Plus E27 Bulb. This is a Multicolor Bulb. We cannot control the color temp.
                        bulbs.append(
                            SengledColorBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
                    if (
                        light["attributes"]["productCode"] == "E11-U3E"
                    ):  # 	Sengled Element Color Plus B22 Bulb. This is a Multicolor Bulb. We cannot control the color temp.
                        bulbs.append(
                            SengledColorBulb(
                                self,
                                light["deviceUuid"],
                                light["attributes"]["name"],
                                ("on" if light["attributes"]["onoff"] == 1 else "off"),
                                light["attributes"]["productCode"],
                                light["attributes"]["brightness"],
                                light["attributes"]["deviceRssi"],
                                light["attributes"]["isOnline"],
                                self._jsession_id,
                                self._country,
                            )
                        )
        if self._wifi:
            for devicebulb in await self.get_devices():
                if devicebulb.type_code == "wificolora19":
                    _LOGGER.debug("SengledAPI: uuid " + devicebulb.uuid)
                    _LOGGER.debug(
                        "SengledAPI: brightness " + str(devicebulb.brightness)
                    )
                    bulbs.append(
                        SengledWifiColorBulb(
                            self,
                            devicebulb.uuid,
                            devicebulb.name,
                            devicebulb.switch,
                            devicebulb.type_code,
                            round((devicebulb.brightness / 100) * 255),
                            devicebulb.color,
                            devicebulb.color_mode,
                            devicebulb.color_temperature,
                            devicebulb.device_rssi,
                            devicebulb.online,
                            self._jsession_id,
                            self._country,
                        )
                    )
                if devicebulb.type_code == "wifia19":
                    bulbs.append(
                        SengledWifiBulb(
                            self,
                            devicebulb.uuid,
                            devicebulb.name,
                            devicebulb.switch,
                            devicebulb.type_code,
                            devicebulb.brightness,
                            devicebulb.device_rssi,
                            devicebulb.online,
                            self._jsession_id,
                            self._country,
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
                                self._country,
                            )
                        )
        return switch

    #######################Do request#######################################################
    async def async_do_request(self, url, payload, jsessionId):
        try:
            return await SengledRequest(url, payload).async_get_response(jsessionId)
        except:
            return SengledRequest(url, payload).get_response(jsessionId)

    ###################################Login Request only###############################
    async def async_do_login_request(self, url, payload):
        _LOGGER.debug("async_do_login_request - Sengled Api doing request.")
        try:
            return await SengledRequest(url, payload).async_get_login_response()
        except:
            return SengledRequest(url, payload).get_login_response()

    ######################################Session Timeout#######################################
    async def async_do_is_session_timeout_request(self, url, payload):
        _LOGGER.debug("async_do_login_request - Sengled Api doing request.")
        try:
            return await SengledRequest(url, payload).async_is_session_timeout_response(
                self._jsession_id
            )
        except:
            return SengledRequest(url, payload).is_session_timeout_response(
                self._jsession_id
            )

    #########################MQTT#################################################
    def _initialize_mqtt(self):
        _LOGGER.debug("Sengledwifi Initialize the MQTT connection")
        """Initialize the MQTT connection."""
        if not self._jsession_id:
            _LOGGER.debug("MQTT _initialize_mqtt no Accesstoken yet")
            return False

        def on_message(client, userdata, msg):
            if msg.topic in self._subscribed:
                _LOGGER.debug(str(self._subscribed))
                _LOGGER.debug(str(userdata))
                _LOGGER.debug(str(self._subscribed[msg.topic](msg.payload)))
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
        _LOGGER.debug("SengledApi: Start mqtt loop %s", format(self._mqtt_client))

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
        _LOGGER.debug("SengledApi: Publish Mqtt %s", str(r))
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
