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

    # regulatedDrive
    def test_regulatedDrive(self):
        hal = self._getStdHal()
        hal.regulatedDrive('B', 'C', False, 'forward', 100)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp, actors['C'].speed_sp)

    # driveDistance
    def test_driveDistance(self):
        hal = self._getStdHal()
        hal.driveDistance('B', 'C', False, 'forward', 100, 10)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp, actors['C'].speed_sp)
        self.assertEqual(actors['B'].position_sp, actors['C'].position_sp)

    # rotateDirectionRegulated
    def test_rotateDirectionRegulated(self):
        hal = self._getStdHal()
        hal.rotateDirectionRegulated('B', 'C', False, 'right', 100)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp, -actors['C'].speed_sp)

    # rotateDirectionAngle
    def test_rotateDirectionAngle(self):
        hal = self._getStdHal()
        hal.rotateDirectionAngle('B', 'C', False, 'right', 100, 90.0)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp, actors['C'].speed_sp)
        self.assertEqual(actors['B'].position_sp, -actors['C'].position_sp)

    # driveInCurve
    def test_driveInCurve_noDist(self):
        hal = self._getStdHal()
        hal.driveInCurve('forward', 'B', 10, 'C', 20)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp * 2, actors['C'].speed_sp)

    def test_driveInCurve_Dist(self):
        hal = self._getStdHal()
        hal.driveInCurve('forward', 'B', 10, 'C', 20, 100)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp * 2, actors['C'].speed_sp)
        self.assertGreater(actors['B'].position_sp, 0)
        self.assertGreater(actors['C'].position_sp, 0)

    def test_driveInCurve_DistBackward(self):
        hal = self._getStdHal()
        hal.driveInCurve('backward', 'B', 10, 'C', 20, 100)
        actors = hal.cfg['actors']
        self.assertEqual(actors['B'].speed_sp * 2, actors['C'].speed_sp)
        self.assertLess(actors['B'].position_sp, 0)
        self.assertLess(actors['C'].position_sp, 0)

    def test_driveInCurve_ZeroSpeed(self):
        hal = self._getStdHal()
        actors = hal.cfg['actors']
        hal.driveInCurve('forward', 'B', 0, 'C', 0, 100)
        self.assertEqual(actors['B'].speed_sp, 0)
        self.assertEqual(actors['C'].speed_sp, 0)

    def test_driveInCurve_OppositeSpeeds(self):
        hal = self._getStdHal()
        actors = hal.cfg['actors']
        hal.driveInCurve('forward', 'B', 10, 'C', -10, 100)
        self.assertEqual(actors['B'].speed_sp, 10)
        self.assertEqual(actors['C'].speed_sp, -10)
