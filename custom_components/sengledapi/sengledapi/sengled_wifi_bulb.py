import asyncio
import logging
from urllib.parse import urlparse
from uuid import uuid4
import json
import paho.mqtt.client as mqtt
import requests
import time

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: sengled_bulb class")

bad_chars = [':'] 

class SengledWifiBulb:
    def __init__(self, client, info):
        """
        Initialize the bulb.
        client -- SengledClient instance this is attached to
        info -- the device info object returned by the server
        """
        self._client = client
        self._uuid = ''.join(i for i in info['deviceUuid'] if not i in bad_chars)
        self._category = info['category']
        self._type_code = info['typeCode']
        self._attributes = info['attributeList']

        self._client._subscribe_mqtt(
            'wifielement/{}/status'.format(self.uuid),
            self._update_status,
        )

    def set_attribute_update_callback(self, callback):
        """
        Set the callback to be called when an attribute is updated.
        callback -- callback
        """
        self._attribute_update_callback = callback

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
            if attr['name'] == 'brightness':
                return self.translate(int(attr['value']), 0, 100, 0, 255)
        return 0

    @property
    def consumption_time(self):
        """Bulb consumption time."""
        for attr in self._attributes:
            if attr['name'] == 'consumptionTime':
                return int(attr['value'], 10)

        return 0

    @property
    def rssi(self):
        """Wi-Fi RSSI."""
        for attr in self._attributes:
            if attr['name'] == 'deviceRssi':
                return int(attr['value'], 10)

        return 0

    @property
    def identify_no(self):
        """Unsure what this is."""
        for attr in self._attributes:
            if attr['name'] == 'identifyNO':
                return attr['value']

        return ''

    @property
    def ip(self):
        """IP address."""
        for attr in self._attributes:
            if attr['name'] == 'ip':
                return attr['value']

        return ''

    @property
    def name(self):
        """Bulb name."""
        for attr in self._attributes:
            if attr['name'] == 'name':
                return attr['value']

        return ''

    @property
    def online(self):
        """Whether or not the bulb is online."""
        for attr in self._attributes:
            if attr['name'] == 'online':
                return 'false' if attr['value'] == '1' else 'false'

        return False

    @property
    def product_code(self):
        """Product code, e.g. 'wifielement'."""
        for attr in self._attributes:
            if attr['name'] == 'product_code':
                return attr['value']

        return ''

    @property
    def save_flag(self):
        """Unsure what this is."""
        for attr in self._attributes:
            if attr['name'] == 'save_flag':
                return attr['value'] == '1'

        return False

    @property
    def start_time(self):
        """Time this device was last connected to network."""
        for attr in self._attributes:
            if attr['name'] == 'start_time':
                return attr['value']

        return ''

    @property
    def support_attributes(self):
        """Unsure what this is."""
        for attr in self._attributes:
            if attr['name'] == 'support_attributes':
                return attr['value']

        return ''

    @property
    def switch(self):
        """Whether or not the bulb is switched on."""
        for attr in self._attributes:
            if attr['name'] == 'switch':
                
                return 'on' if attr['value'] == '1' else "off"
        return "off"

    @property
    def time_zone(self):
        """Time zone of device."""
        for attr in self._attributes:
            if attr['name'] == 'time_zone':
                return attr['value']

        return ''

    @property
    def type_code(self):
        """Type code, e.g. 'wifia19-L'."""
        for attr in self._attributes:
            if attr['name'] == 'type_code':
                return attr['value']

        return self._type_code

    @property
    def version(self):
        """Firmware version."""
        for attr in self._attributes:
            if attr['name'] == 'version':
                return attr['value']

        return ''

    @property
    def uuid(self):
        """Universally unique identifier."""
        return self._uuid

    @property
    def category(self):
        """Category, e.g. 'wifielement'."""
        return self._category

    def toggle(self, on):
        """
        Toggle the state of the bulb.
        on -- whether or not to turn the bulb on
        Returns True on success, False on failure.
        """
        data = {
            'dn': self.uuid,
            'type': 'switch',
            'value': '1' if on else '0',
            'time': int(time.time() * 1000),
        }

        return self._client._publish_mqtt(
            'wifielement/{}/update'.format(self.uuid),
            json.dumps(data),
        )

    def set_brightness(self, level):
        """
        Set the brightness of the bulb.
        level -- new brightness level (0-100)
        Returns True on success, False on failure.
        """
        level = max(min(level, 100), 0)

        data = {
            'dn': self.uuid,
            'type': 'brightness',
            'value': str(level),
            'time': int(time.time() * 1000),
        }

        return self._client._publish_mqtt(
            'wifielement/{}/update'.format(self.uuid),
            json.dumps(data),
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
            if 'type' not in status or 'dn' not in status:
                continue

            if status['dn'] != self.uuid:
                continue

            for attr in self._attributes:
                if attr['name'] == status['type']:
                    attr['value'] = status['value']

                    if self._attribute_update_callback:
                        name = self._attribute_to_property(attr['name'])

                        if hasattr(self, name):
                            self._attribute_update_callback(
                                name,
                                getattr(self, name)
                            )

                    break
 