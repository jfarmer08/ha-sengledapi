"""Sengled Bulb Integration."""

import asyncio
import json
import logging
import time

from .const import (
    HTTPS,
    SET_BRIGHTNESS,
    SET_COLOR_TEMPERATURE,
    SET_GROUP,
)

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
        support_color,
        support_color_temp,
        support_brightness,
        jsession_id,
        country,
        wifi,
    ):
        _LOGGER.info("SengledApi: Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._available = isonline
        self._just_changed_state = True
        self._device_model = device_model
        self._device_rssi = -30
        self._brightness = 255
        self._color = "255:255:255"
        self._color_temperature = None
        self._rgb_color_r = 255
        self._rgb_color_g = 255
        self._rgb_color_b = 255
        self._alarm_status = 0
        self._wifi_device = wifi
        self._support_color = support_color
        self._support_color_temp = support_color_temp
        self._support_brightness = support_brightness
        self._jsession_id = jsession_id
        self._country = country
        # self._api._subscribe_mqtt(
        #    "wifielement/{}/status".format(self._device_mac),
        #    self.update_status,
        # )

    async def async_toggle(self, onoff):
        """Toggle Bulb on or off"""
        if onoff == "1":
            self._state = True
        else:
            self._state = False
        if self._wifi_device:
            _LOGGER.info(
                "SengledApi: Wifi Bulb %s %s turning on.",
                self._friendly_name,
                self._device_mac,
            )
            data = {
                "dn": self._device_mac,
                "type": "switch",
                "value": onoff,
                "time": int(time.time() * 1000),
            }

            self._api.publish_mqtt(
                "wifielement/{}/update".format(self._device_mac),
                json.dumps(data),
            )
        else:
            _LOGGER.info(
                "SengledApi: Bulb %s %s turning on.",
                self._friendly_name,
                self._device_mac,
            )
            url = (
                HTTPS
                + self._country
                + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
            )

            payload = {"deviceUuid": self._device_mac, "onoff": onoff}

            loop = asyncio.get_running_loop()
            loop.create_task(
                self._api.async_do_request(url, payload, self._jsession_id)
            )

    async def async_set_brightness(self, brightness):
        """Set Bulb Brightness"""
        if self._wifi_device:
            _LOGGER.info(
                "Wifi Bulb %s %s setting brightness %s, This is from HA ",
                self._friendly_name,
                self._device_mac,
                str(brightness),
            )

            brightness_precentage = round((brightness / 255) * 100)

            _LOGGER.info(
                "SengledApi: Wifi Color Bulb %s %s setting Brighness %s, This is what we are setting Sengled API",
                self._friendly_name,
                self._device_mac,
                str(brightness_precentage),
            )

            data_brightness = {
                "dn": self._device_mac,
                "type": "brightness",
                "value": str(brightness_precentage),
                "time": int(time.time() * 1000),
            }

            self._api.publish_mqtt(
                "wifielement/{}/update".format(self._device_mac),
                json.dumps(data_brightness),
            )
        else:
            _LOGGER.info(
                "Bulb %s %s setting brightness.", self._friendly_name, self._device_mac
            )

            url = HTTPS + self._country + SET_BRIGHTNESS

            payload = {"deviceUuid": self._device_mac, "brightness": brightness}

            loop = asyncio.get_running_loop()
            loop.create_task(
                self._api.async_do_request(url, payload, self._jsession_id)
            )

    async def async_color_temperature(self, color_temperature):
        _LOGGER.info(
            "Wifi Bulb %s %s setting color Temperature %s, This is from HA ",
            self._friendly_name,
            self._device_mac,
            str(color_temperature),
        )
        """Set Color Temperature"""
        color_temperature_precentage = round(
            self.translate(int(color_temperature), 200, 6500, 1, 100)
        )

        if self._wifi_device:
            _LOGGER.info(
                "SengledApi: Wifi Color Bulb %s %s Set Color Temperature %s, This is what we are setting Sengled API",
                self._friendly_name,
                self._device_mac,
                color_temperature_precentage,
            )

            data_color_temperature = {
                "dn": self._device_mac,
                "type": "colorTemperature",
                "value": str(color_temperature_precentage),
                "time": int(time.time() * 1000),
            }

            self._api.publish_mqtt(
                "wifielement/{}/update".format(self._device_mac),
                json.dumps(data_color_temperature),
            )
        else:
            _LOGGER.info(
                "Bulb %s %s Set Color Temperature %s.",
                self._friendly_name,
                self._device_mac,
                color_temperature_precentage,
            )

            url = HTTPS + self._country + SET_COLOR_TEMPERATURE

            payload = {
                "deviceUuid": self._device_mac,
                "colorTemperature": color_temperature_precentage,
            }

            loop = asyncio.get_running_loop()
            loop.create_task(
                self._api.async_do_request(url, payload, self._jsession_id)
            )

    async def async_set_color(self, color):
        """
        Set the color of a light device.
        device_id: A single device ID or a list to update multiple at once
        color: [red(0-255), green(0-255), blue(0-255)]
        """
        if self._wifi_device:
            _LOGGER.info(
                "SengledApi: Wifi Color Bulb "
                + self._friendly_name
                + " "
                + self._device_mac
                + " .Setting Color"
            )

            data_color = {
                "dn": self._device_mac,
                "type": "color",
                "value": self.convert_color_HA(color),
                "time": int(time.time() * 1000),
            }

            self._api.publish_mqtt(
                "wifielement/{}/update".format(self._device_mac),
                json.dumps(data_color),
            )
        else:
            _LOGGER.info(
                "SengledApi: Color Bulb %s %s Setting Color",
                self._friendly_name,
                self._device_mac,
            )

            mycolor = str(color)
            for r in ((" ", ""), (",", ","), ("(", ""), (")", "")):
                mycolor = mycolor.replace(*r)
                a, b, c = mycolor.split(",")

            _LOGGER.info("SengledApi: Set Color R %s G %s B %s", int(a), int(b), int(c))

            url = HTTPS + self._country + SET_GROUP

            payload = {
                "cmdId": 129,
                "deviceUuidList": [{"deviceUuid": self._device_mac}],
                "rgbColorR": int(a),
                "rgbColorG": int(b),
                "rgbColorB": int(c),
            }

            self._state = True

            loop = asyncio.get_running_loop()
            loop.create_task(
                self._api.async_do_request(url, payload, self._jsession_id)
            )

    def is_on(self):
        """Get State"""
        return self._state

    async def async_update(self):
        if self._wifi_device:
            _LOGGER.info(
                "SengledApi: Wifi Bulb %s %s is updating",
                self._friendly_name,
                self._device_mac,
            )
            if not self._just_changed_state:
                _LOGGER.info(
                    "SengledApi: Bulb State Change: %s", self._just_changed_state
                )
            else:
                bulbs = []
                url = "https://life2.cloud.sengled.com/life2/device/list.json"
                payload = {}

                data = await self._api.async_do_request(url, payload, self._jsession_id)

                _LOGGER.info(
                    "SengledApi: Wifi Bulb " + self._friendly_name + " updating."
                )
                for item in data["deviceList"]:
                    _LOGGER.debug("SengledApi: Wifi Bulb update return: %s", str(item))
                    bulbs.append(BulbProperty(self, item, True))
                for items in bulbs:
                    if items.uuid == self._device_mac:
                        self._friendly_name = items.name
                        self._state = items.switch
                        self._avaliable = items.isOnline
                        self._device_rssi = items.device_rssi
                        # Supported Features
                        if self._support_brightness:
                            self._brightness = round(
                                (int(items.brightness) / 100) * 255
                            )
                        if self._support_color_temp:
                            _LOGGER.debug("SengledApi: Wifi Bulb Colo Temp: %s", items.color_temperature)
                            self._color_temperature = round(self.translate(int(items.color_temperature), 0, 100, 2000, 6500))
                        if self._support_color:
                            _LOGGER.debug("SengledApi: Wifi Bulb Color: %s", items.color)
                            self._color = items.color
        else:
            _LOGGER.info(
                "Sengled Bulb "
                + self._friendly_name
                + " "
                + self._device_mac
                + " updating."
            )
            if self._just_changed_state:
                self._just_changed_state = False
                _LOGGER.info(
                    "SengledApi: Bulb State Change: %s", self._just_changed_state
                )
            else:
                url = "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
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
                                self._device_rssi = round(
                                    self.translate(
                                        int(items.device_rssi), 0, 5, -100, -30
                                    )
                                )
                                # Supported Features
                                if self._support_brightness:
                                    self._brightness = items.brightness
                                if self._support_color:
                                    self._rgb_color_b = items.rgb_color_b
                                    self._rgb_color_g = items.rgb_color_g
                                    self._rgb_color_r = items.rgb_color_r
                                if self._support_color_temp:
                                    _LOGGER.debug(
                                        "color temp %s", items.color_temperature
                                    )
                                    self._color_temperature = items.color_temperature
                                if items.typeCode == "E13-N11":
                                    self._alarm_status = items.alarm_status

    def update_status(self, message):
        """
        Update the status from an incoming MQTT message.
        message -- the incoming message. This is not used.
        """
        try:
            data = json.loads(message)
            _LOGGER.debug("SengledApi: Update Status from MQTT %s", str(data))
        except ValueError:
            return

        for status in data:
            if "type" not in status or "dn" not in status:
                continue

            if status["dn"] == self._device_mac:
                if status["type"] == "color":
                    self._color = status["value"]
                if status["type"] == "colorMode":
                    self._color_mode = status["value"]
                if status["type"] == "brightness":
                    self._brightness = status["value"]
                if status["type"] == "colorTemperature":
                    self._color_temperature = status["value"]

    def set_attribute_update_callback(self, callback):
        """
        Set the callback to be called when an attribute is updated.
        callback -- callback
        """
        self.attribute_update_callback = callback

    @staticmethod
    def attribute_to_property(attr):
        attr_map = {
            "consumptionTime": "consumption_time",
            "deviceRssi": "rssi",
            "identifyNO": "identify_no",
            "productCode": "product_code",
            "saveFlag": "save_flag",
            "startTime": "start_time",
            "supportAttributes": "support_attributes",
            "timeZone": "time_zone",
            "typeCode": "type_code",
        }

        return attr_map.get(attr, attr)

    def convert_color_HA(self, HACOLOR):
        sengled_color = str(HACOLOR)
        for r in ((" ", ""), (",", ":"), ("(", ""), (")", "")):
            sengled_color = sengled_color.replace(*r)
        return sengled_color

    def translate(self, value, left_min, left_max, right_min, right_max):
        """Figure out how 'wide' each range is"""
        left_span = left_max - left_min
        right_span = right_max - right_min

        # Convert the left range into a 0-1 range (float)
        value_scaled = float(value - left_min) / float(left_span)

        # Convert the 0-1 range into a value in the right range.
        return right_min + (value_scaled * right_span)
