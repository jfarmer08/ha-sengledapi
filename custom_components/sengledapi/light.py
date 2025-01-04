#!/usr/bin/python3

"""Platform for light Sengled integration."""

import logging
from datetime import timedelta

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.util import color as colorutil

from .const import ATTRIBUTION, DOMAIN
from .sengledapi.sengledapi import SengledApi

# Add to support quicker update time. Is this to Fast?
SCAN_INTERVAL = timedelta(seconds=10)
ON = "1"
OFF = "0"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Sengled Light platform."""
    _LOGGER.debug("Creating new Sengled light component")
    # Add devices
    add_entities(
        [
            SengledBulb(light)
            for light in await hass.data[DOMAIN][
                "sengledapi_account"
            ].discover_devices()
        ],
        True,
    )


class SengledBulb(LightEntity):
    """Representation of a Sengled Bulb."""

    def __init__(self, light):
        """Initialize a Sengled Bulb."""
        self._light = light
        self._name = light._friendly_name
        self._state = light._state
        self._brightness = light._brightness
        self._available = light._available
        self._device_mac = light._device_mac
        self._device_model = light._device_model
        self._color_temperature = light._color_temperature
        self._color = light._color
        self._device_rssi = light._device_rssi
        self._rgb_color_r = light._rgb_color_r
        self._rgb_color_g = light._rgb_color_g
        self._rgb_color_b = light._rgb_color_b
        self._alarm_status = light._alarm_status
        self._wifi_device = light._wifi_device
        self._support_color = light._support_color
        self._support_color_temp = light._support_color_temp
        self._support_brightness = light._support_brightness

    @property
    def name(self):
        """Return the display name of this light."""
        _LOGGER.debug("Light.py Name %s", self._name)
        return self._name

    @property
    def unique_id(self):
        _LOGGER.debug("Light.py unique_id %s", self._device_mac)
        return self._device_mac

    @property
    def available(self):
        """Return the connection status of this light."""
        _LOGGER.debug("Light.py _available %s", self._available)
        return self._available

    @property
    def extra_state_attributes(self):
        """Return device attributes of the entity."""
        attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "state": self._state,
            "available": self._available,
            "device model": self._device_model,
            "rssi": self._device_rssi,
            "mac": self._device_mac,
            "alarm status ": self._alarm_status,
            "color": self._color,
            "color Temp": self._color_temperature,
            "color r": self._rgb_color_r,
            "color g": self._rgb_color_g,
            "color b": self._rgb_color_b,
        }
        return attributes

    @property
    def color_temp(self):
        """Return the color_temp of the light."""
        _LOGGER.debug("Light.py color_temp %s", self._color_temperature)
        if self._color_temperature is None:
            return colorutil.color_temperature_kelvin_to_mired(2000)
        else:
            return colorutil.color_temperature_kelvin_to_mired(self._color_temperature)

    @property
    def hs_color(self):
        """Return the hs_color of the light."""
        _LOGGER.debug("Light.py hs_color %s", self._color)
        if self._wifi_device:
            a, b, c = self._color.split(":")
            return colorutil.color_RGB_to_hs(int(a), int(b), int(c))
        else:
            return colorutil.color_RGB_to_hs(
                int(self._rgb_color_r), int(self._rgb_color_g), int(self._rgb_color_b)
            )

    @property
    def brightness(self):
        """Return the brightness of the light."""
        _LOGGER.debug("Light.py brightness %s", self._brightness)
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        _LOGGER.debug("Light.py is_on %s", self._state)
        return self._state

    @property
    def supported_color_modes(self):
        """Return the supported color modes for the light."""
        color_modes = set()
        if self._support_brightness:
            color_modes.add(ColorMode.BRIGHTNESS)
        if self._support_color_temp:
            color_modes.add(ColorMode.COLOR_TEMP)
        if self._support_color:
            color_modes.add(ColorMode.HS)
        return color_modes

    @property
    def color_mode(self):
        """Return the current color mode of the light."""
        if self._support_color:
            return ColorMode.HS
        elif self._support_color_temp:
            return ColorMode.COLOR_TEMP
        else:
            return ColorMode.BRIGHTNESS

    async def async_turn_on(self, **kwargs):
        """Turn on or control the light."""
        if not any(
            key in kwargs for key in (ATTR_BRIGHTNESS, ATTR_HS_COLOR, ATTR_COLOR_TEMP)
        ):
            await self._light.async_toggle(ON)
        if ATTR_BRIGHTNESS in kwargs:
            await self._light.async_set_brightness(kwargs[ATTR_BRIGHTNESS])
        if ATTR_HS_COLOR in kwargs:
            hs = kwargs.get(ATTR_HS_COLOR)
            color = colorutil.color_hs_to_RGB(hs[0], hs[1])
            await self._light.async_set_color(color)
        if ATTR_COLOR_TEMP in kwargs:
            color_temp = colorutil.color_temperature_mired_to_kelvin(
                kwargs[ATTR_COLOR_TEMP]
            )
            await self._light.async_color_temperature(color_temp)

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self._light.async_toggle(OFF)

    async def async_update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self._light.async_update()
        self._state = self._light.is_on()
        self._available = self._light._available
        self._state = self._light._state
        self._brightness = self._light._brightness
        self._color_temperature = self._light._color_temperature
        self._color = self._light._color
        self._rgb_color_r = self._light._rgb_color_r
        self._rgb_color_g = self._light._rgb_color_g
        self._rgb_color_b = self._light._rgb_color_b
        self._device_rssi = self._light._device_rssi
        self._alarm_status = self._light._alarm_status

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "name": self._name,
            "identifiers": {(DOMAIN, self._device_mac)},
            "model": self._device_model,
            "manufacturer": "Sengled",
        }
