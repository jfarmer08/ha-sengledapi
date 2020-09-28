"""Sengled Bulb Integration."""

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class Switch:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        accesstoken,
        country,
    ):
        _LOGGER.debug("SengledApi: Switch " + friendly_name + " initializing.")

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._accesstoken = accesstoken
        self._country = country

    async def async_turn_on(self):
        _LOGGER.debug("Switch " + self._friendly_name + " turning on.")

        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )

        payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._accesstoken))

        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug("Switch " + self._friendly_name + " turning off.")

        url = (
            "https://"
            + self._country
            + "-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"
        )

        payload = {"deviceUuid": self._device_mac, "onoff": "0"}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._accesstoken))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug("Switch " + self._friendly_name + " updating.")
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )

            payload = {}
            data = await self._api.async_do_request(url, payload, self._accesstoken)
            _LOGGER.debug("Switch " + self._friendly_name + " updating.")
            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    self._friendly_name = items["attributes"]["name"]
                    self._state = (
                        True if int(items["attributes"]["onoff"]) == 1 else False
                    )
                    self._avaliable = (
                        False if int(items["attributes"]["isOnline"]) == 0 else True
                    )
