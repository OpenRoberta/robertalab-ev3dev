import unittest
import httpretty

from openrobertalab import *


class TestGetHwAddr(unittest.TestCase):
    def test_get_hw_addr(self):
        self.assertRegexpMatches(getHwAddr(b'eth0'), '^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


class TestGenerateToken(unittest.TestCase):
    def test_generate_token(self):
        self.assertRegexpMatches(generateToken(), '^[0-9A-Z]{8}$')


class TestGetBatteryVoltage(unittest.TestCase):
    def test_get_battery_voltage(self):
        self.assertGreaterEqual(float(getBatteryVoltage()), 0.0)


"""
class TestService(unittest.TestCase):
    def test___init__(self):
        # service = Service(path)
        assert False # TODO: implement your test here

    def test_connect(self):
        # service = Service(path)
        # self.assertEqual(expected, service.connect(address))
        assert False # TODO: implement your test here

    def test_disconnect(self):
        # service = Service(path)
        # self.assertEqual(expected, service.disconnect())
        assert False # TODO: implement your test here

    def test_status(self):
        # service = Service(path)
        # self.assertEqual(expected, service.status(status))
        assert False # TODO: implement your test here

class TestHardAbort(unittest.TestCase):
    def test___init__(self):
        # hard_abort = HardAbort(service)
        assert False # TODO: implement your test here

    def test_run(self):
        # hard_abort = HardAbort(service)
        # self.assertEqual(expected, hard_abort.run())
        assert False # TODO: implement your test here

class TestConnector(unittest.TestCase):
    def test___init__(self):
        # connector = Connector(address, service)
        assert False # TODO: implement your test here

    def test_run(self):
        # connector = Connector(address, service)
        # self.assertEqual(expected, connector.run())
        assert False # TODO: implement your test here

    def test_updateConfiguration(self):
        # connector = Connector(address, service)
        # self.assertEqual(expected, connector.updateConfiguration())
        assert False # TODO: implement your test here

class TestCleanup(unittest.TestCase):
    def test_cleanup(self):
        # self.assertEqual(expected, cleanup())
        assert False # TODO: implement your test here

class TestMain(unittest.TestCase):
    def test_main(self):
        # self.assertEqual(expected, main())
        assert False # TODO: implement your test here
"""

if __name__ == '__main__':
    unittest.main()
