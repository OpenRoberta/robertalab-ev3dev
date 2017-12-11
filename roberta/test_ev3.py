import logging
import unittest

from .ev3 import Hal


class TestHal(unittest.TestCase):
    def test__init__(self):
        hal = Hal(None)
