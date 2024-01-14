#!/usr/bin/env python3

import time
import unittest

from pylacus import PyLacus
from pylacus.api import CaptureStatus


class TestBasic(unittest.TestCase):

    def setUp(self) -> None:
        self.client = PyLacus(root_url="http://127.0.0.1:7100")

    def test_up(self) -> None:
        self.assertTrue(self.client.is_up)
        self.assertTrue(self.client.redis_up())

    def test_submit(self) -> None:
        uuid = self.client.enqueue(url="circl.lu")
        while True:
            status = self.client.get_capture_status(uuid)
            if status == CaptureStatus.DONE:
                break
            time.sleep(5)
        response = self.client.get_capture(uuid)
        self.assertEqual(response['status'], 1)
