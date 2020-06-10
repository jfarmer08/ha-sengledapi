import asyncio
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("SengledApi: sengled_bulb class")


class SengledBulb:
    def __init__(
        self,
        api,
        device_mac,
        friendly_name,
        state,
        device_model,
        brightness,
        accesstoken,
    ):
        _LOGGER.debug(
            "SengledApi: Light " + friendly_name + " initializing." + str(accesstoken)
        )

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._brightness = brightness
        self._accesstoken = accesstoken

    async def async_turn_on(self):
        _LOGGER.debug("Farmer: Light " + self._friendly_name + " turning on.")
        if self._brightness is not None:
            url = "https://us-elements.cloud.sengled.com/zigbee/device/deviceSetBrightness.json"

            if self._brightness:
                brightness = self._brightness

            payload = {"deviceUuid": self._device_mac, "brightness": brightness}

        else:
            url = "https://us-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"

            payload = {"deviceUuid": self._device_mac, "onoff": "1"}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._accesstoken))

        self._state = True
        self._just_changed_state = True

    async def async_turn_off(self):
        _LOGGER.debug("Light " + self._friendly_name + " turning off.")
        url = "https://us-elements.cloud.sengled.com/zigbee/device/deviceSetOnOff.json"

        payload = {"deviceUuid": self._device_mac, "onoff": "0"}

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload, self._accesstoken))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug("Light " + self._friendly_name + " updating.")
        if self._just_changed_state:
            self._just_changed_state = False
        else:
            url = (
                "https://element.cloud.sengled.com/zigbee/device/getDeviceDetails.json"
            )
            # url = "https://element.cloud.sengled.com/zigbee/room/getUserRoomsDetail.json"
            payload = {}

            data = await self._api.async_do_request(url, payload, self._accesstoken)
            _LOGGER.debug("Light " + self._friendly_name + " updating." + str(data))
            for item in data["deviceInfos"]:
                for items in item["lampInfos"]:
                    self._friendly_name = items["attributes"]["name"]
                    self._brightness = items["attributes"]["brightness"]
                    self._state = (
                        True if int(items["attributes"]["onoff"]) == 1 else False
                    )
                    self._avaliable = (
                        False if int(items["attributes"]["isOnline"]) == 0 else True
                    )

