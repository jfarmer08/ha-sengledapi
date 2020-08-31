"""Sengled Bulb Integration."""

import asyncio
import logging
import time
import json

from .sengled_wifi_bulb_property import SengledWifiBulbProperty

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: Initializing Sengled Wifi Color Bulb")


class SengledWifiColorBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        isonline,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Wifi Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = isonline
        self._just_changed_state = False
        self._device_model = device_model
        self._jsession_id = jsession_id
        self._device_rssi = None
        self._country = None
        self._brightness = None
        self._color_temperature = None
        self._color = None
        self._rgb_color_r = None
        self._rgb_color_g = None
        self._rgb_color_b = None


    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " .turning on"
        )
        data = {
            "dn": self._device_mac,
            "type": "switch",
            "value": "1",
            "time": int(time.time() * 1000),
        }

        self._api._publish_mqtt(
            "wifielement/{}/update".format(self._device_mac), json.dumps(data),
        )
        self._state = True
        self._just_changed_state = True

    async def async_set_brightness(self, brightness):
        brightness_precentage = round((brightness / 255) * 100)

        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " setting Brightness "
            + str(brightness_precentage)
        )

        data_brightness = {
            "dn": self._device_mac,
            "type": "brightness",
            "value": str(brightness_precentage),
            "time": int(time.time() * 1000),
        }
        self._state = True
        self._just_changed_state = True
        self._api._publish_mqtt(
            "wifielement/{}/update".format(self._device_mac),
            json.dumps(data_brightness),
        )

    async def async_color_temperature(self, colorTemperature):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " .Setting ColorTemp"
        )
        _LOGGER.info("SengledApi: color Temp from HA %s", str(colorTemperature))
        color_temperature_precentage = round(self.translate(int(colorTemperature), 2000, 6500, 1, 100))
        _LOGGER.info("SengledApi: color Temp %s", color_temperature_precentage)
        data_color_temperature = {
            "dn": self._device_mac,
            "type": "colorTemperature",
            "value": str(color_temperature_precentage),
            "time": int(time.time() * 1000),
        }
        self._state = True
        self._just_changed_state = True
        self._api._publish_mqtt(
            "wifielement/{}/update".format(self._device_mac),
            json.dumps(data_color_temperature),
        )

    async def async_set_color(self, color):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " .Setting Color"
        )

        mycolor = str(color)
        for r in ((" ", ""), (",", ":"), ("(",""),(")","")):
            mycolor = mycolor.replace(*r)

        _LOGGER.info("SengledApi: Wifi Set Color %s", str(mycolor))
        data_color = {
            "dn": self._device_mac,
            "type": "color",
            "value": mycolor,
            "time": int(time.time() * 1000),
        }
        self._state = True
        self._just_changed_state = True
        self._api._publish_mqtt(
            "wifielement/{}/update".format(self._device_mac), json.dumps(data_color),
        )

    async def async_turn_off(self):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " turning off."
        )

        data = {
            "dn": self._device_mac,
            "type": "switch",
            "value": "0",
            "time": int(time.time() * 1000),
        }
        self._api._publish_mqtt(
            "wifielement/{}/update".format(self._device_mac), json.dumps(data),
        )
        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug(
            "SengledApi: Wifi Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " updating."
        )
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            bulbs = []
            url = "https://life2.cloud.sengled.com/life2/device/list.json"
            payload = {}

            data = await self._api.async_do_request(url, payload, self._jsession_id)

            _LOGGER.info("SengledApi: Wifi Bulb " + self._friendly_name + " updating.")
            for item in data["deviceList"]:
                # _LOGGER.debug("SengledApi: Wifi Bulb update return " + str(item))
                bulbs.append(SengledWifiBulbProperty(self, item))
            for items in bulbs:
                if items.uuid == self._device_mac:
                    self._friendly_name = items.name
                    self._state = items.switch
                    self._avaliable = items.online
                    self._device_rssi = items.device_rssi
                    #Supported Features
                    self._brightness = round((items.brightness / 100) * 255)
                    self._color_temperature = items.color_temperature
                    self._color = items.color

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)
    def max_kelvin(self):
        _LOGGER.debug("SengledApi: Max Kelvin")
        return 2000
    def min_kelvin(self):
        _LOGGER.debug("SengledApi: Max Kelvin")
        return 6500