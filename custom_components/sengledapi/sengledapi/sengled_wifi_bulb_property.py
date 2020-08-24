"""Sengled Bulb Integration."""


import logging

import json
import time

_LOGGER = logging.getLogger(__name__)


class SengledWifiBulbProperty:
    def __init__(self, client, info):
        """
        Initialize the bulb.
        client -- SengledClient instance this is attached to
        info -- the device info object returned by the server
        """
        self._client = client
        self._uuid = info["deviceUuid"]
        self._category = info["category"]
        self._type_code = info["typeCode"]
        self._attributes = info["attributeList"]

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

    @property
    def brightness(self):
        """Bulb brightness."""
        for attr in self._attributes:
            if attr["name"] == "brightness":
                return round(self.translate(int(attr["value"]), 0, 100, 0, 255), 4)
        return 0

    @property
    def color_temperature(self):
        """Bulb consumption time."""
        for attr in self._attributes:
            if attr["name"] == "colorTemperature":
                return int(attr["value"])
        return 0

    @property
    def color(self):
        """Bulb color."""
        # This is being displayed as RGB
        for attr in self._attributes:
            if attr["name"] == "color":
                return attr["value"]

        return ""

    @property
    def color_mode(self):
        """Bulb consumption time."""
        for attr in self._attributes:
            if attr["name"] == "colorMode":
                return int(attr["value"], 10)

        return 0

    @property
    def consumption_time(self):
        """Bulb consumption time."""
        for attr in self._attributes:
            if attr["name"] == "consumptionTime":
                return int(attr["value"], 10)

        return 0

    @property
    def device_rssi(self):
        """Wi-Fi RSSI."""
        for attr in self._attributes:
            if attr["name"] == "deviceRssi":
                return int(attr["value"], 10)

        return 0

    @property
    def identify_no(self):
        """Unsure what this is."""
        for attr in self._attributes:
            if attr["name"] == "identifyNO":
                return attr["value"]

        return ""

    @property
    def ip(self):
        """IP address."""
        for attr in self._attributes:
            if attr["name"] == "ip":
                return attr["value"]

        return ""

    @property
    def name(self):
        """Bulb name."""
        for attr in self._attributes:
            if attr["name"] == "name":
                return attr["value"]

        return ""

    @property
    def online(self):
        """Whether or not the bulb is online."""
        for attr in self._attributes:
            if attr["name"] == "online":
                return "true" if attr["value"] == "1" else "false"

        return False

    @property
    def product_code(self):
        """Product code, e.g. 'wifielement'."""
        for attr in self._attributes:
            if attr["name"] == "product_code":
                return attr["value"]

        return ""

    @property
    def save_flag(self):
        """Unsure what this is."""
        for attr in self._attributes:
            if attr["name"] == "save_flag":
                return attr["value"] == "1"

        return False

    @property
    def start_time(self):
        """Time this device was last connected to network."""
        for attr in self._attributes:
            if attr["name"] == "start_time":
                return attr["value"]

        return ""

    @property
    def support_attributes(self):
        """Unsure what this is."""
        for attr in self._attributes:
            if attr["name"] == "support_attributes":
                return attr["value"]

        return ""

    @property
    def switch(self):
        """Whether or not the bulb is switched on."""
        for attr in self._attributes:
            if attr["name"] == "switch":
                return True if attr["value"] == "1" else False
        return False

    @property
    def time_zone(self):
        """Time zone of device."""
        for attr in self._attributes:
            if attr["name"] == "time_zone":
                return attr["value"]

        return ""

    @property
    def type_code(self):
        """Type code, e.g. 'wifia19-L'."""
        for attr in self._attributes:
            if attr["name"] == "type_code":
                return attr["value"]

        return self._type_code

    @property
    def version(self):
        """Firmware version."""
        for attr in self._attributes:
            if attr["name"] == "version":
                return attr["value"]

        return ""

    @property
    def uuid(self):
        """Universally unique identifier."""
        return self._uuid

    @property
    def category(self):
        """Category, e.g. 'wifielement'."""
        return self._category
