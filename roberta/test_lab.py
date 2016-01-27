import logging
import httpretty
import unittest

import lab
from lab import Connector, Service

logging.basicConfig(level=logging.DEBUG)

URL = 'http://lab.open-roberta.org'


class TestGetHwAddr(unittest.TestCase):
    def test_get_hw_addr(self):
        self.assertRegexpMatches(lab.getHwAddr(b'eth0'), '^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


class TestGenerateToken(unittest.TestCase):
    def test_generate_token(self):
        self.assertRegexpMatches(lab.generateToken(), '^[0-9A-Z]{8}$')


class TestGetBatteryVoltage(unittest.TestCase):
    def test_get_battery_voltage(self):
        self.assertGreaterEqual(float(lab.getBatteryVoltage()), 0.0)


class TestService(unittest.TestCase):
    def test___init__(self):
        service = Service(None)
        self.assertNotEqual('00:00:00:00:00:00', service.params['macaddr'])

    def test_updateConfiguration(self):
        service = Service(None)
        token = service.params['token']
        service.updateConfiguration()
        self.assertNotEqual(token, service.params['token'])

"""
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
        hard_abort = HardAbort(null)
        assert False # TODO: implement your test here

    def test_run(self):
        # hard_abort = HardAbort(service)
        # self.assertEqual(expected, hard_abort.run())
        assert False # TODO: implement your test here
"""


class TestConnector(unittest.TestCase):
    def test___init__(self):
        connector = Connector(URL, None)
        self.assertTrue(connector.running)

    @httpretty.activate
    def test_run(self):
        httpretty.register_uri(httpretty.POST, "%s/pushcmd" % URL,
                               body='{"success": false}',
                               status=403,
                               content_type='text/json')

        connector = Connector(URL, None)
        connector.run()  # catch error and return


"""
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
