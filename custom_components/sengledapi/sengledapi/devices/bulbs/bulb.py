"""Sengled Bulb Integration."""

import asyncio
import logging

from .bulbproperty import BulbProperty

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("SengledApi: Initializing Bulbs")


class Bulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        isonline,
        support_color_temp,
        support_brightness,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = isonline
        self._just_changed_state = False
        self._device_model = device_model
        self._device_rssi = None
        self._brightness = 0
        self._color = 0
        self._color_temperature = 2000
        self._rgb_color_r = 0
        self._rgb_color_g = 0
        self._rgb_color_b = 0
        self._alarm_status = None
        self._support_color_temp = support_color_temp
        self._support_brightness = support_brightness
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Bulb %s %s turning on.", self._friendly_name, self._device_mac
        )
        self._just_changed_state = True
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )

        payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

        self._state = True
        self._just_changed_state = True

    async def async_set_brightness(self, brightness):
        _LOGGER.debug(
            "Bulb %s %s setting brightness.", self._friendly_name, self._device_mac
        )
        self._state = True
        self._just_changed_state = True

        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"
        )

        payload = {"deviceUuid": self._device_mac, "brightness": brightness}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

    async def async_turn_off(self):
        _LOGGER.debug(
            "SengledApi: Bulb %s %s turning off.", self._friendly_name, self._device_mac
        )

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
            "Sengled Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " updating."
        )
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )
            payload = {}
            bulbs = []
            data = await self._api.async_do_request(url, payload, self._jsession_id)
            for item in data["deviceInfos"]:
                for devices in item["lampInfos"]:
                    bulbs.append(BulbProperty(self, devices, False))
                    for items in bulbs:
                        if items.uuid == self._device_mac:
                            self._friendly_name = items.name
                            self._state = items.switch
                            self._avaliable = items.isOnline
                            self._device_rssi = items.device_rssi
                            # Supported Features
                            self._brightness = items.brightness
                            if items.typeCode == "E13-N11":
                                self._alarm_status = items.alarm_status


class ColorBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        isonline,
        support_color_temp,
        support_brightness,
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
        self._jsession_id = jsession_id
        self._isonline = isonline
        self._country = country
        self._device_rssi = None
        self._support_color_temp = support_color_temp
        self._support_brightness = support_brightness
        # Support Features
        self._brightness = None
        self._color_temperature = 2000
        self._color = None
        self._rgb_color_r = None
        self._rgb_color_g = None
        self._rgb_color_b = None
        self._alarm_status = None

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Color Bulb %s %s turning on.",
            self._friendly_name,
            self._device_mac,
        )

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
            "SengledApi: Color Bulb %s %s setting brightness.",
            self._friendly_name,
            self._device_mac,
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

        _LOGGER.info("SengledApi: color Temp from HA %s", str(colorTemperature))
        color_temperature_percentage = round(
            BulbProperty.translate(
                self,
                int(colorTemperature),
                BulbProperty.max_kelvin,
                BulbProperty.min_kelvin,
                1,
                100,
            )
        )
        _LOGGER.info("SengledApi: color Temp %s", color_temperature_percentage)

        self._just_changed_state = True
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetColorTemperature.json"
        )
        payload = {
            "deviceUuid": self._device_mac,
            "colorTemperature": color_temperature_percentage,
        }
        self._state = True
        self._just_changed_state = True

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

    async def async_set_color(self, color):
        """
        Set the color of a light device.
        device_id: A single device ID or a list to update multiple at once
        color: [red(0-255), green(0-255), blue(0-255)]
        """
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " .Setting Color"
        )

        mycolor = str(color)
        if (
            self._device_model == "E11-N1EA"
            or self._device_model == "E11-U2E"
            or self._device_model == "E11-U3E"
            or self._device_model == "E1G-G8E"
            or self._device_model == "E12-N1E"
        ):
            for r in ((" ", ""), (",", ","), ("(", ""), (")", "")):
                mycolor = mycolor.replace(*r)
                a, b, c = mycolor.split(",")
        if self._device_model == "wifia19" or self._device_model == "wificolora19":
            for r in ((" ", ""), (",", ":"), ("(", ""), (")", "")):
                mycolor = mycolor.replace(*r)
                a, b, c = mycolor.split(":")
        _LOGGER.info("SengledApi: Set Color R %s G %s B %s", int(a), int(b), int(c))

        self._just_changed_state = True
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetGroup.json"
        )

        payload = {
            "cmdId": 129,
            "deviceUuidList": [{"deviceUuid": self._device_mac}],
            "rgbColorR": int(a),
            "rgbColorG": int(b),
            "rgbColorB": int(c),
        }

        self._state = True
        self._just_changed_state = True

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._jsession_id))

    async def async_turn_off(self):
        _LOGGER.debug(
            "SengledApi: Color Bulb %s %s turning on.",
            self._friendly_name,
            self._device_mac,
        )
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
            "SenledApi: Color Bulb %s Mac %s updating.",
            self._friendly_name,
            self._device_mac,
        )

        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )

            payload = {}

            data = await self._api.async_do_request(url, payload, self._jsession_id)

            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    if items["deviceUuid"] == self._device_mac:
                        self._friendly_name = items["attributes"]["name"]
                        self._state = (
                            True if int(items["attributes"]["onoff"]) == 1 else False
                        )
                        self._avaliable = (
                            False if int(items["attributes"]["isOnline"]) == 0 else True
                        )
                        self._device_rssi = BulbProperty.translate(
                            self, int(items["attributes"]["deviceRssi"]), 0, 5, 0, -100
                        )
                        # Supported Features
                        self._brightness = int(items["attributes"]["brightness"])
                        self._color_temperature = round(
                            BulbProperty.translate(
                                self,
                                int(items["attributes"]["colorTemperature"]),
                                0,
                                100,
                                BulbProperty.max_kelvin,
                                BulbProperty.min_kelvin,
                            )
                        )
                        self._rgb_color_r = int(items["attributes"]["rgbColorR"])
                        self._rgb_color_g = int(items["attributes"]["rgbColorG"])
                        self._rgb_color_b = int(items["attributes"]["rgbColorB"])
