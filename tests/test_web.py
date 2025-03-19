#!/usr/bin/env python3

import json
import time
import unittest

from datetime import datetime
from typing import Any

from pylacus import PyLacus
from pylacus.api import CaptureStatus


class TestBasic(unittest.TestCase):

    def setUp(self) -> None:
        self.client = PyLacus(root_url="http://127.0.0.1:7100")

    def test_up(self) -> None:
        self.assertTrue(self.client.redis_up())
        self.assertTrue(self.client.is_up)
        self.assertFalse(self.client.is_busy())

    def test_submit(self) -> None:
        uuid = self.client.enqueue(url="circl.lu", max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        self.assertEqual(response['status'], 1)

    def test_submit_cookies(self) -> None:
        # Very basic cookie
        uuid = self.client.enqueue(url="circl.lu", cookies="{\"test\": \"test\"}", max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        if not response['cookies']:
            self.fail("No cookies found")
        if not response['storage'] or 'cookies' not in response['storage']:
            self.fail("No storage found")
        self.assertEqual(len(response['cookies']), 1)
        self.assertEqual(response['cookies'][0]['domain'], 'circl.lu')
        self.assertEqual(response['cookies'], response['storage']['cookies'])

        cookie_from_capture: dict[str, Any] = response['cookies'][0]
        expires = datetime.now().timestamp() + 3600
        cookie_from_capture['expires'] = expires
        uuid = self.client.enqueue(url="circl.lu", cookies=cookie_from_capture, max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        if not response['cookies']:
            self.fail("No cookies found")
        self.assertEqual(response['cookies'][0]['expires'], expires)

        # Send list
        cookies_from_capture: list[dict[str, Any]] = response['cookies']
        expires = datetime.now().timestamp() + 4000
        cookies_from_capture[0]['expires'] = expires
        uuid = self.client.enqueue(url="circl.lu", cookies=cookies_from_capture, max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        if not response['cookies']:
            self.fail("No cookies found")
        self.assertEqual(response['cookies'][0]['expires'], expires)

        # Send list as json
        cookies_from_capture = response['cookies']
        uuid = self.client.enqueue(url="circl.lu", cookies=json.dumps(cookies_from_capture), max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        if response['cookies']:
            self.assertEqual(response['cookies'][0]['expires'], expires, response['cookies'])

    def test_submit_storage(self) -> None:
        uuid = self.client.enqueue(url="https://mdn.github.io/dom-examples/web-storage/",
                                   max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        storage = response['storage']
        if not storage or 'origins' not in storage or not storage['origins']:
            self.fail("No storage found")
        self.assertEqual(storage['origins'][0]['origin'], 'https://mdn.github.io')
        self.assertEqual(len(storage['origins'][0]['localStorage']), 3)
        for item in storage['origins'][0]['localStorage']:
            if item['name'] == 'font':
                self.assertEqual(item['value'], 'sans-serif')
            elif item['name'] == 'image':
                self.assertEqual(item['value'], 'images/firefoxos.png')
            elif item['name'] == 'bgcolor':
                self.assertEqual(item['value'], 'FF0000')

        # Change values
        for item in storage['origins'][0]['localStorage']:
            if item['name'] == 'font':
                item['value'] = 'serif'
            elif item['name'] == 'image':
                item['value'] = 'images/crocodile.png'
            elif item['name'] == 'bgcolor':
                item['value'] = '00FF00'

        uuid = self.client.enqueue(url="https://mdn.github.io/dom-examples/web-storage/",
                                   storage=storage,
                                   max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        storage = response['storage']
        if not storage or 'origins' not in storage or not storage['origins']:
            self.fail("No storage found")
        self.assertEqual(storage['origins'][0]['origin'], 'https://mdn.github.io')
        self.assertEqual(len(storage['origins'][0]['localStorage']), 3)
        for item in storage['origins'][0]['localStorage']:
            if item['name'] == 'font':
                self.assertEqual(item['value'], 'serif')
            elif item['name'] == 'image':
                self.assertEqual(item['value'], 'images/crocodile.png')
            elif item['name'] == 'bgcolor':
                self.assertEqual(item['value'], '00FF00')

    def test_submit_indexeddb(self) -> None:
        uuid = self.client.enqueue(url="https://mdn.github.io/dom-examples/indexeddb-api/index.html",
                                   # headless=False,
                                   headers={'foo': 'bar'},
                                   max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        storage = response['storage']
        if not storage or 'origins' not in storage or not storage['origins']:
            self.fail("No storage found")
        self.assertEqual(storage['origins'][0]['origin'], 'https://mdn.github.io')
        self.assertEqual(len(storage['origins'][0]['indexedDB']), 1)
        indexeddb = storage['origins'][0]['indexedDB'][0]
        self.assertEqual(indexeddb['name'], 'mdn-demo-indexeddb-epublications')
        self.assertEqual(len(indexeddb['stores'][0]['records']), 0)

        # Add record
        record = {'value': {'biblioid': 'Bar',
                            'title': 'Foo',
                            'year': 1999, 'id': 1}}
        storage['origins'][0]['indexedDB'][0]['stores'][0]['records'].append(record)
        uuid = self.client.enqueue(url="https://mdn.github.io/dom-examples/indexeddb-api/index.html",
                                   # headless=False,
                                   storage=storage,
                                   max_retries=0)
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        storage = response['storage']
        if not storage or 'origins' not in storage or not storage['origins']:
            self.fail("No storage found")
        self.assertEqual(storage['origins'][0]['origin'], 'https://mdn.github.io')
        self.assertEqual(len(storage['origins'][0]['indexedDB']), 1)
        indexeddb = storage['origins'][0]['indexedDB'][0]
        self.assertEqual(indexeddb['name'], 'mdn-demo-indexeddb-epublications')
        self.assertEqual(len(indexeddb['stores'][0]['records']), 1)
