#!/usr/bin/python3

"""Platform for switch integration."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
# Import the device class from the component that you want to support
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import ATTR_ATTRIBUTION

from . import DOMAIN
from .sengledapi.sengledapi import SengledApi

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Data provided by Sengled"


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Sengled Switch platform."""
    _LOGGER.debug("""Creating new SengledApi switch component""")

    # Add devices
    add_entities(
        SengledSwitch(switch)
        for switch in await hass.data[DOMAIN]["sengledapi_account"].async_list_switch()
    )


class SengledSwitch(SwitchDevice):
    """Representation of a Wyze Switch."""

    def __init__(self, switch):
        """Initialize a Wyze Switch."""
        self._switch = switch
        self._name = switch._friendly_name
        self._state = switch._state
        self._avaliable = True
        self._device_mac = switch._device_mac
        self._device_model = switch._device_model

    @property
    def name(self):
        """Return the display name of this switch."""
        return self._name

    @property
    def available(self):
        """Return the connection status of this switch"""
        return self._avaliable

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    @property
    def unique_id(self):
        return self._device_mac

    @property
    def extra_state_attributes(self):
        """Return device attributes of the entity."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "state": self._state,
            "available": self._avaliable,
            "device model": self._device_model,
            "mac": self._device_mac,
        }

    async def async_turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        await self._switch.async_turn_on()

    async def async_turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        await self._switch.async_turn_off()

    async def async_update(self):
        """Fetch new state data for this switch.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self._switch.async_update()
        self._state = self._switch._state
