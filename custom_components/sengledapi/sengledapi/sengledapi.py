#!/usr/bin/python3

import logging

_LOGGER = logging.getLogger(__name__)

from .sengled_request import SengledRequest
from .sengled_bulb import SengledBulb
from .sengledapi_exceptions import SengledApiAccessToken

class SengledApi:
    def __init__(self, user_name, password):
        _LOGGER.debug("Sengled Api initializing.")
        self._user_name = user_name
        self._password = password
        self._device_id = "740447d2-eb6e-11e9-81b4-2a2ae2dbcce4"
        self._in_error_state = False
        self._invalid_access_tokens = []
        self._access_token = None
        # Create device array
        self._all_devices = []

    async def async_init(self):
        _LOGGER.debug("Sengled Api initializing async.")
        self._access_token = await self.async_login(
            self._user_name, self._password, self._device_id
        )
        _LOGGER.debug("sengledapi async_init" + self._access_token)

    async def async_login(self, username, password, device_id):
        _LOGGER.debug("Sengled Api log in async.")
        url = "https://element.cloud.sengled.com/zigbee/customer/login.json"
        payload = {
            "os_type": "android",
            "pwd": password,
            "user": username,
            "uuid": device_id,
        }

        data = await self.async_do_login_request(url, payload)

        try:
            access_token = "JSESSIONID=" + data["jsessionid"]
            _LOGGER.debug("Sengled Api accessToken " + str(access_token))
            self._access_token = access_token
            return access_token
        except:
            return None

    def is_valid_login(self):
        if self._access_token == None:
            return False
        return True

    def valid_access_token(self):
        if self._access_token == None:
            return "none"
        return self._access_token

    async def async_get_devices(self):
        _LOGGER.debug("Sengled Api getting devices.")
        if not self._all_devices:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )
            payload = {}
            data = await self.async_do_request(url, payload, self._access_token)
            self._all_devices = data["deviceInfos"]
        return self._all_devices

    async def async_list_bulbs(self):
        _LOGGER.debug("Sengled Api listing bulbs.")
        bulbs = []
        # This is my room list
        for device in await self.async_get_devices():
            _LOGGER.debug(device)
            if "lampInfos" in device:
                for device in device["lampInfos"]:
                    if(device["attributes"]["productCode"] == "E11-G13"):
                        bulbs.append(
                            SengledBulb(
                                self,
                                device["deviceUuid"],
                                device["attributes"]["name"],
                                ("on" if device["attributes"]["onoff"] == 1 else "off"),
                                device["attributes"]["productCode"],
                                device["attributes"]["brightness"],
                                self._access_token,
                            )
                        )
                    if(device["attributes"]["productCode"] == "E11-G23"):
                        bulbs.append(
                            SengledBulb(
                                self,
                                device["deviceUuid"],
                                device["attributes"]["name"],
                                ("on" if device["attributes"]["onoff"] == 1 else "off"),
                                device["attributes"]["productCode"],
                                device["attributes"]["brightness"],
                                self._access_token,
                            )
                        )
                    if(device["attributes"]["productCode"] == "E1A-AC2"):#Light Currently only one i have
                        bulbs.append(
                            SengledBulb(
                                self,
                                device["deviceUuid"],
                                device["attributes"]["name"],
                                ("on" if device["attributes"]["onoff"] == 1 else "off"),
                                device["attributes"]["productCode"],
                                device["attributes"]["brightness"],
                                self._access_token,
                            )
                        )

        return bulbs

    async def async_do_request(self, url, payload, accesstoken):
        _LOGGER.debug("async_do_request - Sengled Api doing request.")
        try:
            return await SengledRequest(url, payload).async_get_response(accesstoken)
        except:
            return SengledRequest(url, payload).get_response(accesstoken)

    ###################################Login Request only###############################
    async def async_do_login_request(self, url, payload):
        _LOGGER.debug("async_do_login_request - Sengled Api doing request.")
        try:
            return await SengledRequest(url, payload).async_get_login_response()
        except:
            return SengledRequest(url, payload).get_login_response()
