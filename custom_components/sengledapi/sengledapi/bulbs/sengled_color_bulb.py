"""Sengled Bulb Integration."""

import asyncio
import logging

# from .sengled_request import SengledRequest

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: Initializing Sengled color Bulb")


class SengledColorBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        brightness,
        device_rssi,
        isonline,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Color Bulb %s initializing.", friendly_name)

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
        self._color_temperature = None
        self._color = None
        self._device_rssi = device_rssi
        self._isonline = isonline

    async def async_turn_on(self):
        _LOGGER.debug("Bulb %s %s turning on.", self._friendly_name, self._device_mac)

        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )

        payload = {"deviceUuid": self._device_mac, "onoff": "1"}
        self._state = True
        self._just_changed_state = True
        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))


    async def async_set_brightness(self, brightness):
        _LOGGER.debug(
            "Bulb %s %s setting brightness.", self._friendly_name, self._device_mac
        )
        self._just_changed_state = True
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"
        )

        payload = {"deviceUuid": self._device_mac, "brightness": brightness}
        self._state = True
        self._just_changed_state = True
        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

    async def async_color_temperature(self, colorTemperature):
        _LOGGER.debug(
            "Bulb %s %s changing color.", self._friendly_name, self._device_mac
        )
        self._just_changed_state = True
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetColorTemperature.json"
        )

        payload = {"deviceUuid": self._device_mac, "colorTemperature": colorTemperature}

        self._state = True
        self._just_changed_state = True

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

    async def async_turn_off(self):
        _LOGGER.debug("Bulb %s %s turning on.", self._friendly_name, self._device_mac)
        self._just_changed_state = True
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )
        payload = {"deviceUuid": self._device_mac, "onoff": "0"}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug(
            "Light " + self._friendly_name + " " + self._device_mac + " updating."
        )
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )
            payload = {}

            data = await self._api.async_do_request(url, payload, self._jsession_id)

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
