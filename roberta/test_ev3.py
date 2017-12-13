import unittest

from .ev3 import Hal
from .test import Ev3dev as ev3dev


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

    def test__init__with_actor(self):
        brickConfiguration = {
            'wheel-diameter': 5.6,
            'track-width': 18.0,
            'actors': {
                'B': Hal.makeLargeMotor(ev3dev.OUTPUT_B, 'on', 'forward'),
            },
            'sensors': {
            },
        }
        hal = Hal(brickConfiguration)
        self.assertIsNotNone(hal.cfg['actors']['B'])

    def _getStdHal(self):
        brickConfiguration = {
            'wheel-diameter': 5.6,
            'track-width': 18.0,
            'actors': {
                'B': Hal.makeLargeMotor(ev3dev.OUTPUT_B, 'on', 'forward'),
                'C': Hal.makeLargeMotor(ev3dev.OUTPUT_C, 'on', 'forward'),
            },
            'sensors': {
            },
        }
        return Hal(brickConfiguration)

    def test_rotateRegulatedMotor_Degree(self):
        hal = self._getStdHal()
        hal.rotateRegulatedMotor('B', 100, 'degree', 90.0)
        self.assertEqual(100, hal.cfg['actors']['B'].args['speed_sp'])

    def test_rotateRegulatedMotor_Rotations(self):
        hal = self._getStdHal()
        hal.rotateRegulatedMotor('B', 100, 'rotations', 2)
        self.assertEqual(720, hal.cfg['actors']['B'].args['position_sp'])

    def test_rotateRegulatedMotor_SpeedIsClipped(self):
        hal = self._getStdHal()
        hal.rotateRegulatedMotor('B', 500, 'degree', 90.0)
        self.assertEqual(100, hal.cfg['actors']['B'].args['speed_sp'])
