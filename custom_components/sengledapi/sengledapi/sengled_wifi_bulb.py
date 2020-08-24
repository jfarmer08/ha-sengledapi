"""Sengled Bulb Integration."""

import asyncio
import logging
import time
import json

from .sengled_request import SengledRequest
from .sengled_wifi_bulb_property import SengledWifiBulbProperty

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: Initializing Sengled Wifi Bulb")


class SengledWifiBulb:
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
        _LOGGER.debug("SengledApi: Wifi Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = isonline
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = int(brightness)
        self._color_temperature = None
        self._device_rssi = device_rssi
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Wifi Bulb "
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

    async def async_turn_off(self):
        _LOGGER.info(
            "SengledApi: Wifi Bulb "
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

            data = await SengledRequest(url, payload).async_get_response(
                self._jsession_id
            )
            _LOGGER.info("SengledApi: Wifi Bulb " + self._friendly_name + " updating.")
            for item in data["deviceList"]:
                _LOGGER.debug("SengledApi: Wifi Bulb update return " + str(item))
                bulbs.append(SengledWifiBulbProperty(self, item))
            for items in bulbs:
                if items.uuid == self._device_mac:
                    self._friendly_name = items.name
                    self._brightness = items.brightness
                    self._state = items.switch
                    self._avaliable = items.online

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)
