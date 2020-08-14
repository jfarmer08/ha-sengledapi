import asyncio
import logging

from .sengled_request import SengledRequest

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: sengled_bulb class")


class SengledBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        brightness,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Light " + friendly_name + " initializing.")

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = int(brightness)
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug("Light " + self._friendly_name + " " + self._device_mac + " turning on.")

        if self._brightness is not None:
            url = ('https://' + self._country + '-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json')

            if self._brightness:
                brightness = self._brightness

            payload = {
                "deviceUuid": self._device_mac, 
                "brightness": brightness
                }

        else:
            url =('https://'+ self._country + '-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json')

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(SengledRequest(url, payload).async_get_response(self._jsession_id))
        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug("Light " + self._friendly_name + " " + self._device_mac + " turning off.")
        url =('https://'+ self._country+ '-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json')
        payload = {
            "deviceUuid": self._device_mac,
            "onoff": "0"
            }


        loop = asyncio.get_running_loop()
        loop.create_task(SengledRequest(url, payload).async_get_response(self._jsession_id))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug("Sengled Bulb " + self._friendly_name + " " + self._device_mac + " updating.")
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = ('https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json')
            payload = {}

            data = await SengledRequest(url, payload).async_get_response(self._jsession_id)
            _LOGGER.debug("Light " + self._friendly_name + " updating.")
            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    if items['deviceUuid'] == self._device_mac:
                        self._friendly_name = items["attributes"]["name"]
                        self._brightness = int(items["attributes"]["brightness"])
                        self._state = (
                            True if int(items["attributes"]["onoff"]) == 1 else False
                        )
                        self._avaliable = (
                            False if int(items["attributes"]["isOnline"]) == 0 else True
                        )

class SengledColorBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        brightness,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Light " + friendly_name + " initializing.")

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = int(brightness)
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug("Light " + self._friendly_name + " " + self._device_mac + " turning on.")

        if self._brightness is not None:
            url = ('https://' + self._country + '-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json')

            if self._brightness:
                brightness = self._brightness

            payload = {
                "deviceUuid": self._device_mac, 
                "brightness": brightness
                }

        else:
            url =('https://'+ self._country + '-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json')

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(SengledRequest(url, payload).async_get_response(self._jsession_id))
        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug("Light " + self._friendly_name + " " + self._device_mac + " turning off.")
        url =('https://'+ self._country+ '-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json')
        payload = {
            "deviceUuid": self._device_mac,
            "onoff": "0"
            }


        loop = asyncio.get_running_loop()
        loop.create_task(SengledRequest(url, payload).async_get_response(self._jsession_id))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug("Light " + self._friendly_name + " " + self._device_mac + " updating.")
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = ('https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json')
            payload = {}

            data = await SengledRequest(url, payload).async_get_response(self._jsession_id)
            _LOGGER.debug("Light " + self._friendly_name + " updating.")
            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    self._friendly_name = items["attributes"]["name"]
                    self._brightness = int(items["attributes"]["brightness"])
                    self._state = (
                        True if int(items["attributes"]["onoff"]) == 1 else False
                    )
                    self._avaliable = (
                        False if int(items["attributes"]["isOnline"]) == 0 else True
                    )

class SengledWifiColorBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        brightness,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Wifi Color Bulb " + friendly_name + " initializing.")

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = int(brightness)
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug("SengledApi: Wifi Color Bulb " + self._friendly_name + " " + self._device_mac + " turning on.")

        if self._brightness is not None:
            url = ('https://' + self._country + '-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json')

            if self._brightness:
                brightness = self._brightness

            payload = {
                "deviceUuid": self._device_mac, 
                "brightness": brightness
                }

        else:
            url =('https://'+ self._country + '-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json')

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(SengledRequest(url, payload).async_get_response(self._jsession_id))
        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug("SengledApi: Wifi Color Bulb " + self._friendly_name + " " + self._device_mac + " turning off.")
        url =('https://'+ self._country+ '-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json')
        payload = {
            "deviceUuid": self._device_mac,
            "onoff": "0"
            }


        loop = asyncio.get_running_loop()
        loop.create_task(SengledRequest(url, payload).async_get_response(self._jsession_id))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug("Light " + self._friendly_name + " " + self._device_mac + " updating.")
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = ('https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json')
            payload = {}

            data = await SengledRequest(url, payload).async_get_response(self._jsession_id)
            _LOGGER.debug("Light " + self._friendly_name + " updating.")
            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    self._friendly_name = items["attributes"]["name"]
                    self._brightness = int(items["attributes"]["brightness"])
                    self._state = (
                        True if int(items["attributes"]["onoff"]) == 1 else False
                    )
                    self._avaliable = (
                        False if int(items["attributes"]["isOnline"]) == 0 else True
                    )