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

    # rotateRegulatedMotor
    def test_rotateRegulatedMotor_Degree(self):
        hal = self._getStdHal()
        hal.rotateRegulatedMotor('B', 100, 'degree', 90.0)
        self.assertEqual(hal.cfg['actors']['B'].speed_sp, 100)

    def test_rotateRegulatedMotor_Rotations(self):
        hal = self._getStdHal()
        hal.rotateRegulatedMotor('B', 100, 'rotations', 2)
        self.assertEqual(hal.cfg['actors']['B'].position_sp, 720)

    def test_rotateRegulatedMotor_SpeedIsClipped(self):
        hal = self._getStdHal()
        hal.rotateRegulatedMotor('B', 500, 'degree', 90.0)
        self.assertEqual(hal.cfg['actors']['B'].speed_sp, 100)

    # rotateUnregulatedMotor
    def test_rotateUnregulatedMotor_Forward(self):
        hal = self._getStdHal()
        hal.rotateUnregulatedMotor('B', 100, 'power', 100)
        self.assertGreater(hal.cfg['actors']['B'].position, 0)

    def test_rotateUnregulatedMotor_Backward(self):
        hal = self._getStdHal()
        hal.rotateUnregulatedMotor('B', -100, 'power', 100)
        self.assertLess(hal.cfg['actors']['B'].position, 0)

    def test_rotateUnregulatedMotor_SpeedIsClipped(self):
        hal = self._getStdHal()
        hal.rotateUnregulatedMotor('B', 500, 'power', 100)
        self.assertEqual(hal.cfg['actors']['B'].duty_cycle_sp, 100)

    # turnOnRegulatedMotor
    def test_turnOnRegulatedMotor_SpeedIsClipped(self):
        hal = self._getStdHal()
        hal.turnOnRegulatedMotor('B', 500)
        self.assertEqual(hal.cfg['actors']['B'].speed_sp, 100)

    # turnOnUnregulatedMotor
    def test_turnOnUnregulatedMotor_SpeedIsClipped(self):
        hal = self._getStdHal()
        hal.turnOnUnregulatedMotor('B', 500)
        self.assertEqual(hal.cfg['actors']['B'].duty_cycle_sp, 100)

    # stopMotor
    def test_stopMotor_defaultMode(self):
        hal = self._getStdHal()
        hal.stopMotor('B')
        self.assertEqual(hal.cfg['actors']['B'].stop_action, 'coast')

    # stopMotors
    def test_stopMotors(self):
        hal = self._getStdHal()
        hal.stopMotors('B', 'C')
        self.assertEqual(hal.cfg['actors']['B'].stop_action, 'coast')
        self.assertEqual(hal.cfg['actors']['C'].stop_action, 'coast')
