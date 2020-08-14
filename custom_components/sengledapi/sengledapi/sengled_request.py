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
        #self._access_token = None
        self._jsession_id = None

        self._header = {
            "Content-Type": "application/json",
            "Host": "element.cloud.sengled.com:443",
            "Connection": "keep-alive",
        }

    def get_response(self, jsession_id):
        self._header = {
            "Content-Type": "application/json",
            'Cookie': 'JSESSIONID={}'.format(jsession_id),
            "Connection": "keep-alive",
        }
        _LOGGER.debug(
            "SengledApi: get_response Sengled Request getting response NON-async."
        )
        r = requests.post(self._url, headers=self._header, data=self._payload)
        data = r.json()
        return data

    async def async_get_response(self, jsession_id):
        self._header = {
            "Content-Type": "application/json",
            'Cookie': 'JSESSIONID={}'.format(jsession_id),
            "Host": "element.cloud.sengled.com:443",
            "Connection": "keep-alive",
        }
        _LOGGER.debug(
            "SengledApi: async_get_response Sengled Request getting response async."
        )
        _LOGGER.debug(self._url)
        _LOGGER.debug(self._header)
        _LOGGER.debug(self._payload)
        async with aiohttp.ClientSession() as session:
            sslcontext = ssl.create_default_context(cafile=certifi.where())
            async with session.post(
                self._url, headers=self._header, data=self._payload, ssl=sslcontext
            ) as resp:
                data = await resp.json()
                _LOGGER.debug("SengledApi: data from async_get_response " + str(data))
                return data

########################Login#####################################
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

######################Session Timeout#################################
    def is_session_timeout_response(self, jsession_id):
        self._header = {
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID={}'.format(jsession_id),
            'sid': jsession_id,
            'X-Requested-With': 'com.sengled.life2',
        }
        _LOGGER.debug(
            "SengledApi: Data from is_session_timeout_response"
        )
        r = requests.post(self._url, headers=self._header, data=self._payload)
        data = r.json()
        return data

    async def async_is_session_timeout_response(self, jsession_id):
        _LOGGER.debug(
            "SengledApi: async_get_login_response Sengled Request getting response async."
        )
        self._header = {
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID={}'.format(jsession_id),
            'sid': jsession_id,
            'X-Requested-With': 'com.sengled.life2',
        }
        async with aiohttp.ClientSession() as session:
            sslcontext = ssl.create_default_context(cafile=certifi.where())
            async with session.post(
                self._url, headers=self._header, data=self._payload, ssl=sslcontext
            ) as resp:
                data = await resp.json()
                _LOGGER.debug("SengledApi: Data from async_is_session_timeout_response " + str(data))
                return data