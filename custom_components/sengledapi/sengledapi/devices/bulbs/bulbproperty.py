"""Sengled Bulb Integration."""


import json
import logging
import time

_LOGGER = logging.getLogger(__name__)


class BulbProperty:
    def __init__(self, api, info, wifi):
        """
        Initialize the bulb.
        api -- Sengledapi instance this is attached to
        info -- the device info object returned by the server
        """
        _LOGGER.debug("SengledApi: Bulb Property - %s", info)
        self._api = api
        self._wifi = wifi
        if wifi:
            self._uuid = info["deviceUuid"]
            self._category = info["category"]
            self._type_code = info["typeCode"]
            self._attributes = info["attributeList"]
        else:
            self._uuid = info["deviceUuid"]
            self.device_class = info["deviceClass"]
            self._attributes = info["attributes"]
            self._info = info

    @property
    def brightness(self):
        """Bulb brightness."""
        if self._wifi:
            for attr in self._attributes:
                if attr["name"] == "brightness":
                    return int(attr["value"], 10)
            return 0
        else:
            if self._attributes["brightness"]:
                brightness = self._info["attributes"]["brightness"]
                return int(brightness)

    @property
    def color_temperature(self):
        """Bulb Temperature."""
        """
        Set the color temperature of a light device.
        temperature: 0 (warm) - 100 (cold)
        """
        if self._wifi:
            for attr in self._attributes:
                if attr["name"] == "colorTemperature":
                    return int(attr["value"])
                #return 2000
        else:
            if self._attributes["colorTemperature"]:
                color_temperature = self._info["attributes"]["colorTemperature"]
                return int(color_temperature)

    @property
    def color_mode(self):
        """Bulb consumption time."""
        if self._wifi:
            for attr in self._attributes:
                if attr["colorMode"] == "colorMode":
                    return int(attr["value"], 10)
            return 0
        else:
            if self._attributes["colorMode"]:
                colorMode = self._info["attributes"]["colorMode"]
                return colorMode

    @property
    def device_rssi(self):
        """Wi-Fi RSSI."""
        if self._wifi:
            for attr in self._attributes:
                if attr["name"] == "deviceRssi":
                    return int(attr["value"], 10)

            return 0
        else:
            if self._attributes["deviceRssi"]:
                device_rssi = self._info["attributes"]["deviceRssi"]
                return device_rssi

    @property
    def name(self):
        """Bulb name."""
        if self._wifi:
            for attr in self._attributes:
                if attr["name"] == "name":
                    return attr["value"]

            return ""
        else:
            if self._attributes["name"]:
                name = self._info["attributes"]["name"]
                return name

    @property
    def switch(self):
        """Whether or not the bulb is switched on."""
        if self._wifi:

            for attr in self._attributes:
                if attr["name"] == "switch":
                    return True if attr["value"] == "1" else False
        else:
            if self._attributes:
                onoff = self._info["attributes"]["onoff"]
                return True if onoff == "1" else False

    @property
    def isOnline(self):
        """Whether or not the bulb is online."""
        if self._wifi:
            for attr in self._attributes:
                if attr["name"] == "online":
                    return True if attr["value"] == "1" else False
        else:
            if self._attributes:
                online = self._info["attributes"]["isOnline"]
                return True if online == "1" else False

    @property
    def typeCode(self):
        """Product code."""
        if self._wifi:
            """Type code, e.g. 'wifia19-L'."""
            for attr in self._attributes:
                if attr["name"] == "typeCode":
                    return attr["value"]
        else:
            if self._attributes:
                typecode = self._info["attributes"]["typeCode"]
                return typecode

    @property
    def productCode(self):
        """Product code"""
        if self._wifi:
            """Product code, e.g. 'wifielement'."""
            for attr in self._attributes:
                if attr["name"] == "product_code":
                    return attr["value"]
        else:
            if self._attributes["productCode"]:
                productCode = self._info["attributes"]["productCode"]
                return productCode

    @property
    def version(self):
        """Firmware version."""
        if self._wifi:
            for attr in self._attributes:
                if attr["version"] == "version":
                    return attr["value"]
        else:
            if self._attributes["version"]:
                version = self._info["attributes"]["version"]
                return version

    @property
    def uuid(self):
        """Universally unique identifier."""
        return self._uuid

    ##Hub property
    @property
    def alarm_status(self):
        """Gets the alarm Status"""
        if self._attributes["alarmStatus"]:
            alarm_status = self._info["attributes"]["alarmStatus"]
            return alarm_status

    @property
    def active_time(self):
        if self._attributes["name"]:
            name = self._info["attributes"]["name"]
            return name

    @property
    def rgb_color_r(self):
        if self._attributes["rgbColorR"]:
            rgbColorR = self._info["attributes"]["rgbColorR"]
            return rgbColorR

    @property
    def rgb_color_g(self):
        if self._attributes["rgbColorG"]:
            rgbColorG = self._info["attributes"]["rgbColorG"]
            return rgbColorG

    @property
    def rgb_color_b(self):
        if self._attributes["rgbColorB"]:
            rgbColorB = self._info["attributes"]["rgbColorB"]
            return rgbColorB

    ###Wifi only Property
    @property
    def color(self):
        """Bulb color."""
        # This is being displayed as RGB
        for attr in self._attributes:
            if attr["name"] == "color":
                return attr["value"]
        return "0:0:0"

    @property
    def consumption_time(self):
        """Bulb consumption time."""
        for attr in self._attributes:
            if attr["name"] == "consumptionTime":
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
    def time_zone(self):
        """Time zone of device."""
        for attr in self._attributes:
            if attr["name"] == "time_zone":
                return attr["value"]

        return ""

    @property
    def category(self):
        """Category, e.g. 'wifielement'."""
        return self._category

    ##########################
    @property
    def max_kelvin(self):
        return 2000

    @property
    def min_kelvin(self):
        return 6500

    ##########################
    @property
    def support_brightness(self):
        """Bulb brightness."""
        try:
            if self._wifi:
                for attr in self._attributes:
                    if attr["name"] == "brightness":
                        return True
            else:
                if self._attributes["brightness"]:
                    brightness = self._info["attributes"]["brightness"]
                    return True
        except:
            return False

    @property
    def support_color_temp(self):
        try:
            if self._wifi:
                for attr in self._attributes:
                    if attr["name"] == "colorTemperature":
                        return True
            else:
                if self._attributes["colorTemperature"]:
                    color_temperature = self._info["attributes"]["colorTemperature"]
                    return True
        except:
            return False

    @property
    def support_color(self):
        """Support Bulb color."""
        try:
            if self._wifi:
                # This is being displayed as RGB
                for attr in self._attributes:
                    if attr["name"] == "color":
                        return True
            else:
                if self._attributes["rgbColorR"]:
                    rgbColorR = self._info["attributes"]["rgbColorR"]
                    return True
        except:
            return False
