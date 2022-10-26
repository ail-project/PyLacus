#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from base64 import b64decode
from enum import IntEnum, unique
from pathlib import Path
from typing import Literal, Optional, Union, Dict, List, Any, TypedDict, overload, cast
from urllib.parse import urljoin, urlparse

import requests

BROWSER = Literal['chromium', 'firefox', 'webkit']


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
    last_redirected_url: Optional[str]
    har: Optional[Dict[str, Any]]
    cookies: Optional[List[Dict[str, str]]]
    error: Optional[str]
    html: Optional[str]
    png: Optional[bytes]
    downloaded_filename: Optional[str]
    downloaded_file: Optional[bytes]
    children: Optional[List[Any]]
    runtime: Optional[float]


class CaptureResponseJson(TypedDict, total=False):
    '''A capture made by Lacus. With the base64 encoded image and downloaded file *not* decoded.'''

    status: int
    last_redirected_url: Optional[str]
    har: Optional[Dict[str, Any]]
    cookies: Optional[List[Dict[str, str]]]
    error: Optional[str]
    html: Optional[str]
    png: Optional[str]
    downloaded_filename: Optional[str]
    downloaded_file: Optional[str]
    children: Optional[List[Any]]
    runtime: Optional[float]


class CaptureSettings(TypedDict, total=False):
    '''The capture settings that can be passed to Lacus.'''

    url: Optional[str]
    document_name: Optional[str]
    document: Optional[str]
    browser: Optional[str]
    device_name: Optional[str]
    user_agent: Optional[str]
    proxy: Optional[Union[str, Dict[str, str]]]
    general_timeout_in_sec: Optional[int]
    cookies: Optional[List[Dict[str, Any]]]
    headers: Optional[Union[str, Dict[str, str]]]
    http_credentials: Optional[Dict[str, int]]
    viewport: Optional[Dict[str, int]]
    referer: Optional[str]
    force: Optional[bool]
    recapture_interval: Optional[int]
    priority: Optional[int]

    depth: int
    rendered_hostname_only: bool  # Note: only used if depth is > 0


class PyLacus():

    def __init__(self, root_url: str):
        '''Query a specific instance.

        :param root_url: URL of the instance to query.
        '''
        self.root_url = root_url

        if not urlparse(self.root_url).scheme:
            self.root_url = 'http://' + self.root_url
        if not self.root_url.endswith('/'):
            self.root_url += '/'
        self.session = requests.session()

    @property
    def is_up(self) -> bool:
        '''Test if the given instance is accessible'''
        try:
            r = self.session.head(self.root_url, timeout=2.0)
        except requests.exceptions.ConnectionError:
            return False
        return r.status_code == 200

    def redis_up(self) -> Dict:
        '''Check if redis is up and running'''
        r = self.session.get(urljoin(self.root_url, 'redis_up'))
        return r.json()

    @overload
    def enqueue(self, *, settings: Optional[CaptureSettings]=None) -> str:
        ...

    @overload
    def enqueue(self, *,
                url: Optional[str]=None,
                document_name: Optional[str]=None, document: Optional[str]=None,
                depth: int=0,
                browser: Optional[BROWSER]=None, device_name: Optional[str]=None,
                user_agent: Optional[str]=None,
                proxy: Optional[Union[str, Dict[str, str]]]=None,
                general_timeout_in_sec: Optional[int]=None,
                cookies: Optional[List[Dict[str, Any]]]=None,
                headers: Optional[Union[str, Dict[str, str]]]=None,
                http_credentials: Optional[Dict[str, int]]=None,
                viewport: Optional[Dict[str, int]]=None,
                referer: Optional[str]=None,
                rendered_hostname_only: bool=True,
                force: bool=False,
                recapture_interval: int=300,
                priority: int=0
                ) -> str:
        ...

    def enqueue(self, *,
                settings: Optional[CaptureSettings]=None,
                url: Optional[str]=None,
                document_name: Optional[str]=None, document: Optional[str]=None,
                depth: int=0,
                browser: Optional[BROWSER]=None, device_name: Optional[str]=None,
                user_agent: Optional[str]=None,
                proxy: Optional[Union[str, Dict[str, str]]]=None,
                general_timeout_in_sec: Optional[int]=None,
                cookies: Optional[List[Dict[str, Any]]]=None,
                headers: Optional[Union[str, Dict[str, str]]]=None,
                http_credentials: Optional[Dict[str, int]]=None,
                viewport: Optional[Dict[str, int]]=None,
                referer: Optional[str]=None,
                rendered_hostname_only: bool=True,
                force: bool=False,
                recapture_interval: int=300,
                priority: int=0
                ) -> str:
        '''Submit a new capture. Pass a typed dictionary or any of the relevant settings, get the UUID.'''
        to_enqueue: CaptureSettings
        if settings:
            to_enqueue = settings
        else:
            to_enqueue = {'depth': depth, 'rendered_hostname_only': rendered_hostname_only,
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
            if headers:
                to_enqueue['headers'] = headers
            if http_credentials:
                to_enqueue['http_credentials'] = http_credentials
            if viewport:
                to_enqueue['viewport'] = viewport
            if referer:
                to_enqueue['referer'] = referer

        r = self.session.post(urljoin(self.root_url, 'enqueue'), json=to_enqueue)
        return r.json()

    def get_capture_status(self, uuid: str) -> CaptureStatus:
        '''Get the status of the capture.'''
        r = self.session.get(urljoin(self.root_url, str(Path('capture_status', uuid))))
        return r.json()

    def _decode_response(self, capture: CaptureResponseJson) -> CaptureResponse:
        decoded_capture = cast(CaptureResponse, capture)
        if capture.get('png') and capture['png']:
            decoded_capture['png'] = b64decode(capture['png'])
        if capture.get('downloaded_file') and capture['downloaded_file']:
            decoded_capture['downloaded_file'] = b64decode(capture['downloaded_file'])
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

    def get_capture(self, uuid: str, *, decode: bool=True) -> Union[CaptureResponse, CaptureResponseJson]:
        '''Get the the capture, with the screenshot and downloaded file decoded to bytes or base64 encoded.'''
        r = self.session.get(urljoin(self.root_url, str(Path('capture_result', uuid))))
        response: CaptureResponseJson = r.json()
        if not decode:
            return response
        return self._decode_response(response)
