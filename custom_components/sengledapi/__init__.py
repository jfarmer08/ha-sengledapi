"""Sengled Bulb Integration."""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (CONF_DEVICES, CONF_PASSWORD, CONF_TIMEOUT,
                                 CONF_USERNAME)
from homeassistant.helpers import discovery

from .const import CONF_COUNTRY, CONF_TYPE, DOMAIN
from .sengledapi.sengledapi import SengledApi

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_COUNTRY): cv.string,
                vol.Optional(CONF_TYPE, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    if conf is not None:
        """Set up the SengledApi parent component."""
        _LOGGER.info(
            """
    -------------------------------------------------------------------
    Sengled Bulb Home Assistant Integration Created from Config

    Version: v0.2
    This is a custom integration
    If you have any issues with this you need to open an issue here:
    https://github.com/jfarmer08/ha-sengledapi
    -------------------------------------------------------------------"""
        )
        _LOGGER.info("""Creating new SengledApi component""")

        sengledapi_account = SengledApi(
            config[DOMAIN].get(CONF_USERNAME),
            config[DOMAIN].get(CONF_PASSWORD),
            config[DOMAIN].get(CONF_COUNTRY),
            config[DOMAIN].get(CONF_TYPE),
        )
        await sengledapi_account.async_init()

        if not sengledapi_account.is_valid_login():
            _LOGGER.error(
                "SengledApi Not connected to Sengled account. Unable to add devices. Check your configuration."
            )
            return False

        _LOGGER.info("SengledApi Connected to Sengled account")

        sengledapi_devices = await sengledapi_account.async_get_devices()
        sengledapiwifi_devices = await sengledapi_account.async_get_wifi_devices()

        # Store the logged in account object for the platforms to use.
        _LOGGER.info(
            "SengledApi Store the logged in account object for the platforms to use"
        )
        hass.data[DOMAIN] = {"sengledapi_account": sengledapi_account}

        _LOGGER.info("SengledApi Start up lights, switch and binary sensor components")
        # Start up lights and switch components
        if sengledapi_devices:
            await discovery.async_load_platform(hass, "light", DOMAIN, {}, config)
        elif sengledapiwifi_devices:
            await discovery.async_load_platform(hass, "light", DOMAIN, {}, config)
        else:
            _LOGGER.error(
                "SengledApi: SengledApi authenticated but could not find any devices."
            )

    return True


async def async_setup_entry(hass, entry):
    """Set up Sengled platform."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    country = entry.data[CONF_COUNTRY]
    bulbtype = entry.data[CONF_TYPE]

    sengledapi_account = SengledApi(
        username,
        password,
        country,
        bulbtype,
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

    return False
