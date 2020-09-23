"""Config flow for Sengled."""
import logging

from .sengledapi.sengledapi import SengledApi

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_PLATFORM, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN, CONF_COUNTRY, CONF_TYPE

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_COUNTRY): str,
        vol.Required(CONF_TYPE): bool,
    }
)


class SengledConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Sengled config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._country = None
        self._password = None
        self._type = True
        self._username = None
        self._is_import = False

    def _get_entry(self):
        return self.async_create_entry(
            title=self._username,
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_COUNTRY: self._country,
                CONF_TYPE: self._type,
            },
        )

    async def _try_connect(self):
        """Try to connect and check auth."""

        """Set up the SengledApi parent component."""
        _LOGGER.debug(
            """
    -------------------------------------------------------------------
    Sengled Bulb Home Assistant Integration Created from ConfigFlow

    Version: v0.1-beta.9
    This is a custom integration
    If you have any issues with this you need to open an issue here:
    https://github.com/jfarmer08/ha-sengledapi
    -------------------------------------------------------------------"""
        )
        _LOGGER.debug("""Creating new SengledApi component""")

        sengledapi_account = SengledApi(
            self._username, self._password, self._country_code, self._type,
        )
        # await sengledapi_account.async_init()

        # if not sengledapi_account.is_valid_login():
        #    _LOGGER.error(
        #        "SengledApi Not connected to Sengled account. Unable to add devices. Check your configuration."
        #    )
        #    return False

        _LOGGER.debug("SengledApi Connected to Sengled account")

        # sengledapi_devices = await sengledapi_account.async_get_devices()

        # Store the logged in account object for the platforms to use.
        _LOGGER.debug(
            "SengledApi Store the logged in account object for the platforms to use"
        )

        return True

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        self._is_import = True
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:

            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._country = str(user_input[CONF_COUNTRY])
            self._type = bool(user_input[CONF_TYPE])

            # result = await self.hass.async_add_executor_job(self._try_connect)

            # if result == True:
            #    return self._get_entry()
            # if result != False or self._is_import:
            #    if self._is_import:
            #        _LOGGER.error(
            #            "Error importing from configuration.yaml: %s",
            #        )
            #    return self.async_abort(reason=result)
            # errors["base"] = result

        return self._get_entry()
