"""Sengled Bulb Integration."""

import asyncio
import logging

from .sengled_request import SengledRequest
from .sengled_wifi_bulb import SengledWifiBulbProp

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
        _LOGGER.debug("SengledApi: Bulb %s initializing.", friendly_name)

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

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Bulb %s %s turning on.", self._friendly_name, self._device_mac
        )

        if self._brightness is not None:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"
            )

            if self._brightness:
                brightness = self._brightness

            payload = {"deviceUuid": self._device_mac, "brightness": brightness}

        else:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
            )

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )
        self._state = True
        self._just_changed_state = True

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
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )

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

            data = await SengledRequest(url, payload).async_get_response(
                self._jsession_id
            )
            _LOGGER.debug("Light " + self._friendly_name + " updating.")
            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    if items["deviceUuid"] == self._device_mac:
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

    async def async_turn_on(self):
        _LOGGER.debug("Bulb %s %s turning on.", self._friendly_name, self._device_mac)

        if self._brightness is not None:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"
            )

            if self._brightness:
                brightness = self._brightness

            payload = {"deviceUuid": self._device_mac, "brightness": brightness}

        else:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
            )

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )
        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug("Bulb %s %s turning on.", self._friendly_name, self._device_mac)
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )
        payload = {"deviceUuid": self._device_mac, "onoff": "0"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )

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

            data = await SengledRequest(url, payload).async_get_response(
                self._jsession_id
            )
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


class SengledWifiBulb:
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
        _LOGGER.debug("SengledApi: Wifi Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = int(brightness)
        self._color_temperature = None
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " turning on."
        )

        if self._brightness is not None:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"
            )

            if self._brightness:
                brightness = self._brightness

            payload = {"deviceUuid": self._device_mac, "brightness": brightness}

        else:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
            )

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )
        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " turning off."
        )
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )
        payload = {"deviceUuid": self._device_mac, "onoff": "0"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    def toggle(self, on):
        """
        Toggle the state of the bulb.
        on -- whether or not to turn the bulb on
        Returns True on success, False on failure.
        """
        data = {
            "dn": self.uuid,
            "type": "switch",
            "value": "1" if on else "0",
            "time": int(time.time() * 1000),
        }

        return self._client._publish_mqtt(
            "wifielement/{}/update".format(self.uuid), json.dumps(data),
        )

    def set_brightness(self, level):
        """
        Set the brightness of the bulb.
        level -- new brightness level (0-100)
        Returns True on success, False on failure.
        """
        level = max(min(level, 100), 0)

        data = {
            "dn": self.uuid,
            "type": "brightness",
            "value": str(level),
            "time": int(time.time() * 1000),
        }

        return self._client._publish_mqtt(
            "wifielement/{}/update".format(self.uuid), json.dumps(data),
        )

    def _update_status(self, message):
        """
        Update the status from an incoming MQTT message.
        message -- the incoming message
        """
        try:
            data = json.loads(message)
        except ValueError:
            return

        for status in data:
            if "type" not in status or "dn" not in status:
                continue

            if status["dn"] != self.uuid:
                continue

            for attr in self._attributes:
                if attr["name"] == status["type"]:
                    attr["value"] = status["value"]

                    if self._attribute_update_callback:
                        name = self._attribute_to_property(attr["name"])

                        if hasattr(self, name):
                            self._attribute_update_callback(name, getattr(self, name))

                    break

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
            _LOGGER.debug("SengledApi: Wifi Bulb " + self._friendly_name + " updating.")
            for item in data["deviceList"]:
                _LOGGER.debug("SengledApi: Wifi Bulb update return " + str(item))
                bulbs.append(SengledWifiBulbProp(self, item))
            for items in bulbs:
                self._friendly_name = items.name
                self._brightness = items.brightness
                self._state = items.switch
                self._avaliable = items.online


class SengledWifiColorBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        brightness,
        color,
        color_mode,
        color_temperature,
        jsession_id,
        country,
    ):
        _LOGGER.debug("SengledApi: Wifi Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = int(brightness)
        self._color_temperature = self.translate(
            int(color_temperature), 0, 100, 0, 10000
        )
        self._jsession_id = jsession_id
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " turning on."
        )

        if self._brightness is not None:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"
            )

            if self._brightness:
                brightness = self._brightness

            payload = {"deviceUuid": self._device_mac, "brightness": brightness}

        else:
            url = (
                "https://"
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
            )

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )
        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug(
            "SengledApi: Wifi Color Bulb "
            + self._friendly_name
            + " "
            + self._device_mac
            + " turning off."
        )
        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )
        payload = {"deviceUuid": self._device_mac, "onoff": "0"}

        loop = asyncio.get_running_loop()
        loop.create_task(
            SengledRequest(url, payload).async_get_response(self._jsession_id)
        )

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    def toggle(self, on):
        """
        Toggle the state of the bulb.
        on -- whether or not to turn the bulb on
        Returns True on success, False on failure.
        """
        data = {
            "dn": self.uuid,
            "type": "switch",
            "value": "1" if on else "0",
            "time": int(time.time() * 1000),
        }

        return self._client._publish_mqtt(
            "wifielement/{}/update".format(self.uuid), json.dumps(data),
        )

    def set_brightness(self, level):
        """
        Set the brightness of the bulb.
        level -- new brightness level (0-100)
        Returns True on success, False on failure.
        """
        level = max(min(level, 100), 0)

        data = {
            "dn": self.uuid,
            "type": "brightness",
            "value": str(level),
            "time": int(time.time() * 1000),
        }

        return self._client._publish_mqtt(
            "wifielement/{}/update".format(self.uuid), json.dumps(data),
        )

    def _update_status(self, message):
        """
        Update the status from an incoming MQTT message.
        message -- the incoming message
        """
        try:
            data = json.loads(message)
        except ValueError:
            return

        for status in data:
            if "type" not in status or "dn" not in status:
                continue

            if status["dn"] != self.uuid:
                continue

            for attr in self._attributes:
                if attr["name"] == status["type"]:
                    attr["value"] = status["value"]

                    if self._attribute_update_callback:
                        name = self._attribute_to_property(attr["name"])

                        if hasattr(self, name):
                            self._attribute_update_callback(name, getattr(self, name))

                    break

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
            _LOGGER.debug("SengledApi: Wifi Bulb " + self._friendly_name + " updating.")
            for item in data["deviceList"]:
                _LOGGER.debug("SengledApi: Wifi Bulb update return " + str(item))
                bulbs.append(SengledWifiBulbProp(self, item))
            for items in bulbs:
                self._friendly_name = items.name
                self._brightness = items.brightness
                self._state = items.switch
                self._avaliable = items.online
                self._color_temperature = self.translate(
                    int(items.color_temperature), 0, 100, 0, 10000
                )
                _LOGGER.debug(items.brightness)
                _LOGGER.debug(items.color_temperature)

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)
