#!/usr/bin/python3

"""Platform for light integration."""
import logging
from .sengledapi.sengledapi import SengledApi
from . import DOMAIN


import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import ATTR_ATTRIBUTION

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Data provided by Sengled"


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Sengled Light platform."""
    _LOGGER.debug("""Creating new Sengled light component""")
    # Add devices
    add_entities(
        SengledBulb(light)
        for light in await hass.data[DOMAIN]["sengledapi_account"].async_list_bulbs()
    )


class SengledBulb(LightEntity):
    """Representation of a Sengled Bulb."""

    def __init__(self, light):
        """Initialize a Sengled Bulb."""
        self._light = light
        self._name = light._friendly_name
        self._state = light._state
        self._brightness = light._brightness
        self._avaliable = True
        self._device_mac = light._device_mac
        self._device_model = light._device_model

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self):
        return self._device_mac

    @property
    def available(self):
        """Return the connection status of this light"""
        return self._avaliable

    @property
    def device_state_attributes(self):
        """Return device attributes of the entity."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "state": self._state,
            "available": self._avaliable,
            "device model": self._device_model,
            #            "ssid": self._ssid,
            #           "ip": self._ip,
            #            "rssi": self._rssi,
            "mac": self._device_mac,
        }

    @property
    def brightness(self):
        """Return the brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._light._brightness = kwargs.get(ATTR_BRIGHTNESS)
        await self._light.async_turn_on()

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self._light.async_turn_off()

    async def async_update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self._light.async_update()
        self._state = self._light.is_on()
        self._avaliable = self._light._avaliable
        self._brightness = self._light._brightness
