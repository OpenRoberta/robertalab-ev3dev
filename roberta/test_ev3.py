import unittest

from .ev3 import Hal


class TestHal(unittest.TestCase):
    def test__init__no_cfg(self):
        hal = Hal(None)
        self.assertNotEqual(0, hal.font_w)
        self.assertNotEqual(0, hal.font_h)

    def test__init__simple_cfg(self):
        brickConfiguration = {
            'wheel-diameter': 5.6,
            'track-width': 18.0,
            'actors': {
            },
            'sensors': {
            },
        }
        hal = Hal(brickConfiguration)
        self.assertIn('wheel-diameter', hal.cfg)
