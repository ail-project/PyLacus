#!/usr/bin/env python3

from __future__ import annotations

from base64 import b64decode
from datetime import datetime, date
from enum import IntEnum, unique
from importlib.metadata import version
from pathlib import PurePosixPath
from typing import Literal, Any, TypedDict, overload, cast
from urllib.parse import urljoin, urlparse

import requests

from urllib3.util import Retry
from requests.adapters import HTTPAdapter

BROWSER = Literal['chromium', 'firefox', 'webkit']


# Clone of the TypedDict from Playwright to keep i consntent with LacusCore
class Cookie(TypedDict, total=False):
    name: str
    value: str
    domain: str
    path: str
    expires: float
    httpOnly: bool
    secure: bool
    sameSite: Literal["Lax", "None", "Strict"]


@unique
class CaptureStatus(IntEnum):
    '''The status of the capture'''
    UNKNOWN = -1
    QUEUED = 0
    DONE = 1
    ONGOING = 2


class CaptureResponse(TypedDict, total=False):
    '''A capture made by Lacus. With the base64 encoded image and downloaded file decoded to bytes.'''

    status: int
    last_redirected_url: str | None
    har: dict[str, Any] | None
    cookies: list[dict[str, str]] | None
    storage: dict[str, Any] | None
    error: str | None
    html: str | None
    png: bytes | None
    downloaded_filename: str | None
    downloaded_file: bytes | None
    children: list[Any] | None
    runtime: float | None
    potential_favicons: set[bytes] | None


class CaptureResponseJson(TypedDict, total=False):
    '''A capture made by Lacus. With the base64 encoded image and downloaded file *not* decoded.'''

    status: int
    last_redirected_url: str | None
    har: dict[str, Any] | None
    cookies: list[dict[str, str]] | None
    storage: dict[str, Any] | None
    error: str | None
    html: str | None
    png: str | None
    downloaded_filename: str | None
    downloaded_file: str | None
    children: list[Any] | None
    runtime: float | None
    potential_favicons: list[str] | None


class CaptureSettings(TypedDict, total=False):
    '''The capture settings that can be passed to Lacus.'''

    url: str | None
    document_name: str | None
    document: str | None
    browser: Literal['chromium', 'firefox', 'webkit'] | None
    device_name: str | None
    user_agent: str | None
    proxy: str | dict[str, str] | None
    general_timeout_in_sec: int | None
    cookies: str | dict[str, str] | list[Cookie] | list[dict[str, Any]] | None
    storage: str | dict[str, Any] | None
    headers: str | dict[str, str] | None
    http_credentials: dict[str, str] | None
    geolocation: dict[str, str | int | float] | None
    timezone_id: str | None
    locale: str | None
    color_scheme: str | None
    java_script_enabled: bool
    viewport: dict[str, int | str] | None
    referer: str | None
    with_screenshot: bool
    with_favicon: bool
    allow_tracking: bool
    headless: bool

    force: bool | None
    recapture_interval: int | None
    priority: int | None
    max_retries: int | None
    uuid: str | None

    depth: int
    rendered_hostname_only: bool  # Note: only used if depth is > 0


class PyLacus():

    def __init__(self, root_url: str, useragent: str | None=None,
                 *, proxies: dict[str, str] | None=None) -> None:
        '''Query a specific instance.

        :param root_url: URL of the instance to query.
        :param useragent: The User Agent used by requests to run the HTTP requests against Lacus, it is *not* passed to the captures.
        :param proxies: The proxies to use to connect to lacus (not the ones given to the capture itself) - More details: https://requests.readthedocs.io/en/latest/user/advanced/#proxies
        '''
        self.root_url = root_url

        if not urlparse(self.root_url).scheme:
            self.root_url = 'http://' + self.root_url
        if not self.root_url.endswith('/'):
            self.root_url += '/'
        self.session = requests.session()
        self.session.headers['user-agent'] = useragent if useragent else f'PyLacus / {version("pylacus")}'
        if proxies:
            self.session.proxies.update(proxies)
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    @property
    def is_up(self) -> bool:
        '''Test if the given instance is accessible'''
        try:
            r = self.session.head(self.root_url, timeout=2.0)
        except requests.exceptions.ConnectionError:
            return False
        return r.status_code == 200

    def redis_up(self) -> dict[str, Any]:
        '''Check if redis is up and running'''
        r = self.session.get(urljoin(self.root_url, 'redis_up'))
        return r.json()

    @overload
    def enqueue(self, *, settings: CaptureSettings | None=None) -> str:
        ...

    @overload
    def enqueue(self, *,
                url: str | None=None,
                document_name: str | None=None, document: str | None=None,
                depth: int=0,
                browser: BROWSER | None=None, device_name: str | None=None,
                user_agent: str | None=None,
                proxy: str | dict[str, str] | None=None,
                general_timeout_in_sec: int | None=None,
                cookies: str | dict[str, str] | list[dict[str, Any]] | list[Cookie] | None=None,
                storage: str | dict[str, Any] | None=None,
                headers: str | dict[str, str] | None=None,
                http_credentials: dict[str, str] | None=None,
                geolocation: dict[str, str | int | float] | None=None,
                timezone_id: str | None=None,
                locale: str | None=None,
                color_scheme: str | None=None,
                java_script_enabled: bool=True,
                viewport: dict[str, str | int] | None=None,
                referer: str | None=None,
                with_screenshot: bool=True,
                with_favicon: bool=False,
                allow_tracking: bool=False,
                headless: bool=True,
                rendered_hostname_only: bool=True,
                force: bool=False,
                recapture_interval: int=300,
                priority: int=0,
                max_retries: int | None=None,
                uuid: str | None=None,
                ) -> str:
        ...

    def enqueue(self, *,
                settings: CaptureSettings | None=None,
                url: str | None=None,
                document_name: str | None=None, document: str | None=None,
                depth: int=0,
                browser: BROWSER | None=None, device_name: str | None=None,
                user_agent: str | None=None,
                proxy: str | dict[str, str] | None=None,
                general_timeout_in_sec: int | None=None,
                cookies: str | dict[str, str] | list[dict[str, Any]] | list[Cookie] | None=None,
                storage: str | dict[str, Any] | None=None,
                headers: str | dict[str, str] | None=None,
                http_credentials: dict[str, str] | None=None,
                geolocation: dict[str, str | int | float] | None=None,
                timezone_id: str | None=None,
                locale: str | None=None,
                color_scheme: str | None=None,
                java_script_enabled: bool=True,
                viewport: dict[str, str | int] | None=None,
                referer: str | None=None,
                with_screenshot: bool=True,
                with_favicon: bool=False,
                allow_tracking: bool=False,
                headless: bool=True,
                rendered_hostname_only: bool=True,
                force: bool=False,
                recapture_interval: int=300,
                priority: int=0,
                max_retries: int | None=None,
                uuid: str | None=None,
                ) -> str:
        '''Submit a new capture. Pass a typed dictionary or any of the relevant settings, get the UUID.'''
        to_enqueue: CaptureSettings
        if settings:
            to_enqueue = settings
        else:
            to_enqueue = {'depth': depth, 'java_script_enabled': java_script_enabled,
                          'with_favicon': with_favicon, 'allow_tracking': allow_tracking,
                          'headless': headless, 'with_screenshot': with_screenshot,
                          'rendered_hostname_only': rendered_hostname_only,
                          'force': force, 'recapture_interval': recapture_interval, 'priority': priority}
            if url:
                to_enqueue['url'] = url
            elif document_name and document:
                to_enqueue['document_name'] = document_name
                to_enqueue['document'] = document
            if browser:
                to_enqueue['browser'] = browser
            if device_name:
                to_enqueue['device_name'] = device_name
            if user_agent:
                to_enqueue['user_agent'] = user_agent
            if proxy:
                to_enqueue['proxy'] = proxy
            if general_timeout_in_sec is not None:  # that would be a terrible idea, but this one could be 0
                to_enqueue['general_timeout_in_sec'] = general_timeout_in_sec
            if cookies:
                to_enqueue['cookies'] = cookies
            if storage:
                to_enqueue['storage'] = storage
            if headers:
                to_enqueue['headers'] = headers
            if http_credentials:
                to_enqueue['http_credentials'] = http_credentials
            if geolocation:
                to_enqueue['geolocation'] = geolocation
            if timezone_id:
                to_enqueue['timezone_id'] = timezone_id
            if locale:
                to_enqueue['locale'] = locale
            if color_scheme:
                to_enqueue['color_scheme'] = color_scheme
            if viewport:
                to_enqueue['viewport'] = viewport
            if referer:
                to_enqueue['referer'] = referer
            if max_retries is not None:
                to_enqueue['max_retries'] = max_retries
            if uuid:
                to_enqueue['uuid'] = uuid

        r = self.session.post(urljoin(self.root_url, 'enqueue'), json=to_enqueue)
        return r.json()

    def get_capture_status(self, uuid: str) -> CaptureStatus:
        '''Get the status of the capture.'''
        r = self.session.get(urljoin(self.root_url, str(PurePosixPath('capture_status', uuid))))
        return r.json()

    def _decode_response(self, capture: CaptureResponseJson) -> CaptureResponse:
        decoded_capture = cast(CaptureResponse, capture)
        if capture.get('png') and capture['png']:
            decoded_capture['png'] = b64decode(capture['png'])
        if capture.get('downloaded_file') and capture['downloaded_file']:
            decoded_capture['downloaded_file'] = b64decode(capture['downloaded_file'])
        if capture.get('potential_favicons') and capture['potential_favicons']:
            decoded_capture['potential_favicons'] = {b64decode(f) for f in capture['potential_favicons']}
        if capture.get('children') and capture['children']:
            for child in capture['children']:
                child = self._decode_response(child)
        return decoded_capture

    @overload
    def get_capture(self, uuid: str, *, decode: Literal[True]=True) -> CaptureResponse:
        ...

    @overload
    def get_capture(self, uuid: str, *, decode: Literal[False]) -> CaptureResponseJson:
        ...

    def get_capture(self, uuid: str, *, decode: bool=True) -> CaptureResponse | CaptureResponseJson:
        '''Get the the capture, with the screenshot and downloaded file decoded to bytes or base64 encoded.'''
        r = self.session.get(urljoin(self.root_url, str(PurePosixPath('capture_result', uuid))))
        response: CaptureResponseJson = r.json()
        if not decode:
            return response
        return self._decode_response(response)

    def push_capture(self, uuid: str, push_to: str) -> dict[str, Any]:
        '''Push the capture to a specific endpoint.

        :param uuid: UUID of the capture to push (in the lacus instance you are querying).
        :param push_to: Endpoint to push the results of the capture to.
        '''
        results = self.get_capture(uuid, decode=False)
        response = requests.post(push_to, json=results)
        return response.json()

    # # Stats and status of the lacus instance

    def daily_stats(self, d: str | date | datetime | None=None, /, *, cardinality_only: bool=True) -> dict[str, Any]:
        '''Get the stats for a specific day (only the last few days are stored in lacus).

        :param cardinality_only: If True, only return the number of entries in each list (captures, retries, failed retries), instead of the URLs.
        '''
        if cardinality_only:
            url_path = PurePosixPath('daily_stats')
        else:
            url_path = PurePosixPath('daily_stats_details')

        if d:
            if isinstance(d, (date, datetime)):
                url_path /= d.isoformat()
            else:
                url_path /= d

        r = self.session.get(urljoin(self.root_url, str(url_path)))
        return r.json()

    def db_status(self) -> dict[str, Any]:
        '''Gets the database status (number of keys, memory usage)'''
        r = self.session.get(urljoin(self.root_url, 'db_status'))
        return r.json()

    def ongoing_captures(self, *, with_settings: bool=False) -> list[dict[str, Any]]:
        r = self.session.get(urljoin(self.root_url, 'ongoing_captures'),
                             params={'with_settings': True} if with_settings else {})
        return r.json()

    def enqueued_captures(self, *, with_settings: bool=False) -> list[dict[str, Any]]:
        r = self.session.get(urljoin(self.root_url, 'enqueued_captures'),
                             params={'with_settings': True} if with_settings else {})
        return r.json()

    def status(self) -> dict[str, Any]:
        '''Get the status of the instance.'''
        r = self.session.get(urljoin(self.root_url, 'lacus_status'))
        return r.json()

    def is_busy(self) -> bool:
        '''Check if the instance is busy.'''
        r = self.session.get(urljoin(self.root_url, 'is_busy'))
        return r.json()

    def proxies(self) -> dict[str, Any]:
        '''Get the proxies enabled on the instance.'''
        r = self.session.get(urljoin(self.root_url, 'proxies'))
        return r.json()
