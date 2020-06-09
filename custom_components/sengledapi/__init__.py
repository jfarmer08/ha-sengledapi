"""Sengled Bulb Integration."""

import logging

import voluptuous as vol

from .sengledapi.sengledapi import SengledApi

from homeassistant.const import CONF_DEVICES, CONF_PASSWORD, CONF_TIMEOUT, CONF_USERNAME
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sengledapi"
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the SengledApi parent component."""
    _LOGGER.debug(
        """
-------------------------------------------------------------------
Sengled Bulb Home Assistant Integration

Version: v0.0.1
This is a custom integration
If you have any issues with this you need to open an issue here:

-------------------------------------------------------------------"""
    )
    _LOGGER.debug("""Creating new SengledApi component""")

    sengledapi_account = SengledApi(
        config[DOMAIN].get(CONF_USERNAME), config[DOMAIN].get(CONF_PASSWORD)
    )
    await sengledapi_account.async_init()

    if not sengledapi_account.is_valid_login():
        _LOGGER.error(
            "SengledApi Not connected to Sengled account. Unable to add devices. Check your configuration."
        )
        return False

    _LOGGER.debug("SengledApi Connected to Sengled account")

    sengledapi_devices = await sengledapi_account.async_get_devices()

    # Store the logged in account object for the platforms to use.
    _LOGGER.debug(
        "SengledApi Store the logged in account object for the platforms to use"
    )
    hass.data[DOMAIN] = {"sengledapi_account": sengledapi_account}

    _LOGGER.debug("SengledApi Start up lights, switch and binary sensor components")
    # Start up lights and switch components
    if sengledapi_devices:
        await discovery.async_load_platform(hass, "light", DOMAIN, {}, config)
    else:
        _LOGGER.error(
            "SengledApi: SengledApi authenticated but could not find any devices."
        )

    return True
