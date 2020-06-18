import requests
import json
import aiohttp
import ssl
import certifi
import logging


_LOGGER = logging.getLogger(__name__)
from .sengledapi_exceptions import SengledApiAccessToken


class SengledRequest:
    def __init__(self, url, payload, no_return=False):
        _LOGGER.debug("SengledApi: Sengled Request initializing.")
        self._url = url
        self._payload = json.dumps(payload)
        self._no_return = no_return
        self._response = None
        self._access_token = None

        self._header = {
            "Content-Type": "application/json",
            "Host": "element.cloud.sengled.com:443",
            "Connection": "keep-alive",
        }

    def get_response(self, access_token):
        self._header = {
            "Content-Type": "application/json",
            "Cookie": access_token,
            "Connection": "keep-alive",
        }
        _LOGGER.debug(
            "SengledApi: get_response Sengled Request getting response NON-async."
        )
        r = requests.post(self._url, headers=self._header, data=self._payload)
        data = r.json()
        return data

    async def async_get_response(self, access_token):
        self._header = {
            "Content-Type": "application/json",
            "Cookie": access_token,
            "Host": "element.cloud.sengled.com:443",
            "Connection": "keep-alive",
        }
        _LOGGER.debug(
            "SengledApi: async_get_response Sengled Request getting response async."
        )
        async with aiohttp.ClientSession() as session:
            sslcontext = ssl.create_default_context(cafile=certifi.where())
            async with session.post(
                self._url, headers=self._header, data=self._payload, ssl=sslcontext
            ) as resp:
                data = await resp.json()
                _LOGGER.debug("SengledApi: data from async_get_response " + str(data))
                return data

    def get_login_response(self):
        _LOGGER.debug(
            "SengledApi: get_login_response Sengled Request getting response."
        )
        r = requests.post(self._url, headers=self._header, data=self._payload)
        data = r.json()
        _LOGGER.debug("SengledApi: data from get_response " + str(data))
        return data

    async def async_get_login_response(self):
        _LOGGER.debug(
            "SengledApi: async_get_login_response Sengled Request getting response async."
        )
        async with aiohttp.ClientSession() as session:
            sslcontext = ssl.create_default_context(cafile=certifi.where())
            async with session.post(
                self._url, headers=self._header, data=self._payload, ssl=sslcontext
            ) as resp:
                data = await resp.json()
                _LOGGER.debug("SengledApi: data from async_get_response " + str(data))
                return data
