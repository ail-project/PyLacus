#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from base64 import b64decode
from enum import IntEnum, unique
from pathlib import Path
from typing import Literal, Optional, Union, Dict, List, Any, TypedDict, overload, cast
from urllib.parse import urljoin, urlparse

import requests


@unique
class CaptureStatus(IntEnum):
    UNKNOWN = -1
    QUEUED = 0
    DONE = 1
    ONGOING = 2


class CaptureResponse(TypedDict, total=False):

    status: int
    last_redirected_url: str
    har: Optional[Dict[str, Any]]
    cookies: Optional[List[Dict[str, str]]]
    error: Optional[str]
    html: Optional[str]
    png: Optional[bytes]
    downloaded_filename: Optional[str]
    downloaded_file: Optional[bytes]
    children: Optional[List[Any]]


class CaptureResponseJson(TypedDict, total=False):

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


class CaptureSettings(TypedDict, total=False):

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

    depth: Optional[int]
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
        r = self.session.head(self.root_url)
        return r.status_code == 200

    def redis_up(self) -> Dict:
        '''Check if redis is up and running'''
        r = self.session.get(urljoin(self.root_url, 'redis_up'))
        return r.json()

    def enqueue(self, settings: CaptureSettings) -> str:
        r = self.session.post(urljoin(self.root_url, 'enqueue'), json=settings)
        return r.json()

    def capture_status(self, uuid: str) -> CaptureStatus:
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
    def capture_result(self, uuid: str, *, decode: Literal[True]=True) -> CaptureResponse:
        ...

    @overload
    def capture_result(self, uuid: str, *, decode: Literal[False]) -> CaptureResponseJson:
        ...

    def capture_result(self, uuid: str, *, decode: bool=True) -> Union[CaptureResponse, CaptureResponseJson]:
        r = self.session.get(urljoin(self.root_url, str(Path('capture_result', uuid))))
        response: CaptureResponseJson = r.json()
        if not decode:
            return response
        return self._decode_response(response)
