#!/usr/bin/python3

"""Platform for light integration."""

import logging
from .sengledapi.sengledapi import SengledApi
from .const import ATTRIBUTION, DOMAIN

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.util import color as colorutil

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ATTR_COLOR_TEMP,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    LightEntity,
)


_LOGGER = logging.getLogger(__name__)


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
        self._color_temperature = light._color_temperature

    @property
    def name(self):
        """Return the display name of this light."""
        # pylint:disable=logging-not-lazy
        _LOGGER.debug(
            "SengledApi Light "
            + self._name
            + " State "
            + str(self._state)
            + " Brightness "
            + str(self._brightness)
            + " Avaliable "
            + str(self._avaliable)
            + " Devive Mac "
            + str(self._device_mac)
            + " Device Model "
            + str(self._device_model)
        )
        return self._name

    @property
    def unique_id(self):
        # pylint:disable=logging-not-lazy
        _LOGGER.debug(
            "SengledApi Light "
            + self._name
            + " State "
            + str(self._state)
            + " Brightness "
            + str(self._brightness)
            + " Avaliable "
            + str(self._avaliable)
            + " Devive Mac "
            + str(self._device_mac)
            + " Device Model "
            + str(self._device_model)
        )
        return self._device_mac

    @property
    def available(self):
        # pylint:disable=logging-not-lazy
        """Return the connection status of this light"""
        _LOGGER.debug(
            "SengledApi Light "
            + self._name
            + " State "
            + str(self._state)
            + " Brightness "
            + str(self._brightness)
            + " Avaliable "
            + str(self._avaliable)
            + " Devive Mac "
            + str(self._device_mac)
            + " Device Model "
            + str(self._device_model)
        )
        return self._avaliable

    @property
    def device_state_attributes(self):
        # pylint:disable=logging-not-lazy
        """Return device attributes of the entity."""
        _LOGGER.debug(
            "SengledApi Light "
            + self._name
            + " State "
            + str(self._state)
            + " Brightness "
            + str(self._brightness)
            + " Avaliable "
            + str(self._avaliable)
            + " Devive Mac "
            + str(self._device_mac)
            + " Device Model "
            + str(self._device_model)
        )
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "state": self._state,
            "available": self._avaliable,
            "device model": self._device_model,
            "mac": self._device_mac,
        }

    @property
    def color_temp(self):
        """Return the color_temp of the light."""
        color_temp = self._color_temperature
        if color_temp is None:
            return 1
        return color_temp

    @property
    def brightness(self):
        # pylint:disable=logging-not-lazy
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
        features = SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_COLOR
        if self._device_model != "wificolora19":
            features = SUPPORT_BRIGHTNESS
        return features

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on. """
        if self._device_model != "wificolora19":
            self._light._brightness = kwargs.get(ATTR_BRIGHTNESS)
            # self._light._colortemp = kwargs.get(ATTR_COLOR_TEMP)
            await self._light.async_turn_on()

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        if self._device_model != "wificolora19":
            await self._light.async_turn_off()

    async def async_update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self._light.async_update()
        self._state = self._light.is_on()
        self._avaliable = self._light._avaliable
        self._brightness = self._light._brightness
        self._color_temperature = self._color_temperature
