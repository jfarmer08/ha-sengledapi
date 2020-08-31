"""Sengled Bulb Integration."""

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: Initializing Sengled Bulb")


class SengledBulbFloodMotion:
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
        _LOGGER.debug("SengledApi: Bulb %s initializing.", friendly_name)

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = isonline
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = None
        self._jsession_id = jsession_id
        self._country = country
        self._color_temperature = None
        self._color = None
        self._device_rssi = None
        self._rgb_color_r = None
        self._rgb_color_g = None
        self._rgb_color_b = None
        #self._api._subscribe_mqtt('wifielement/{}/status'.format(self._device_mac),self._update_status,)
        _LOGGER.debug("  ")

    async def async_turn_on(self):
        _LOGGER.debug(
            "SengledApi: Bulb %s %s turning on.", self._friendly_name, self._device_mac
        )

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

            data = await self._api.async_do_request(url, payload, self._jsession_id)

            _LOGGER.debug("Light " + self._friendly_name + " updating.")
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
                        self._device_rssi = self.translate(int(items["attributes"]["deviceRssi"]), 0, 5, 0, -100)
                        #Support Features
                        self._brightness = int(items["attributes"]["brightness"])

    def _update_status(self, message):
        """
        Update the status from an incoming MQTT message.
        message -- the incoming message
        """
        try:
            data = json.loads(message)
            _LOGGER.debug("SengledAPI: Farmer Update Status from MQTT %s", str(data))
        except ValueError:
            return

        for status in data:
            if 'type' not in status or 'dn' not in status:
                continue

    def set_attribute_update_callback(self, callback):
        """
        Set the callback to be called when an attribute is updated.
        callback -- callback
        """
        self._attribute_update_callback = callback

    @staticmethod
    def _attribute_to_property(attr):
        attr_map = {
            'consumptionTime': 'consumption_time',
            'deviceRssi': 'rssi',
            'identifyNO': 'identify_no',
            'productCode': 'product_code',
            'saveFlag': 'save_flag',
            'startTime': 'start_time',
            'supportAttributes': 'support_attributes',
            'timeZone': 'time_zone',
            'typeCode': 'type_code',
        }

        return attr_map.get(attr, attr)

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)
