import logging
import httpretty
import _thread
import threading
import time
import unittest

from roberta import lab
from roberta.lab import Connector, Service, TOKEN_PER_SESSION

from .test import Hal
from .__version__ import version

logging.basicConfig(level=logging.DEBUG)

URL = 'http://lab.open-roberta.org'
JSON = 'application/json'
CMD_REPEAT = '{"cmd": "repeat"}'


class DummyAbortHandler(threading.Thread):
    def __init__(self, to_sleep=0.0):
        threading.Thread.__init__(self)
        self.running = True
        self.to_sleep = to_sleep

    def run(self):
        if self.to_sleep:
            time.sleep(self.to_sleep)
            _thread.interrupt_main()

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        if type is not None:  # an exception has occurred
            return False      # reraise the exception


class DummyService(object):
    def __init__(self):
        self.hal = Hal(None)
        self.params = {
            'macaddr': '00:00:00:00:00:00',
            'firmwarename': 'ev3dev',
            'menuversion': version.split('-')[0],
        }
        self.last_status = None

    def status(self, status):
        self.last_status = status


class TestGetHwAddr(unittest.TestCase):
    def test_get_hw_addr(self):
        self.assertRegex(lab.getHwAddr(b'eth0'), '^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


class TestGenerateToken(unittest.TestCase):
    def test_generate_token(self):
        self.assertRegex(lab.generateToken(), '^[0-9A-Z]{8}$')


class TestGetBatteryVoltage(unittest.TestCase):
    def test_get_battery_voltage(self):
        self.assertGreaterEqual(float(lab.getBatteryVoltage()), 0.0)


class TestService(unittest.TestCase):
    def test___init__(self):
        service = Service(None)
        self.assertNotEqual('00:00:00:00:00:00', service.params['macaddr'])

    def test_updateConfiguration(self):
        if TOKEN_PER_SESSION:
            return
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

class TestAbortHandler(unittest.TestCase):
    def test___init__(self):
        abort_handler = AbortHandler(null)
        assert False # TODO: implement your test here

    def test_run(self):
        # abort_handler = AbortHandler(service)
        # self.assertEqual(expected, abort_handler.run())
        assert False # TODO: implement your test here
"""


class TestConnector(unittest.TestCase):
    GOOD_CODE = (
        'if __name__ == "__main__":\n'
        '  pass\n'
    )
    BAD_CODE = (
        '{ this is not python, right?\n'
    )
    GOOD_CODE_WITH_RESULT = (
        'if __name__ == "__main__":\n'
        '  result = 42\n'
    )
    INFINITE_LOOP = (
        'import time\n'
        'result=0\n'
        'while True:\n'
        '  time.sleep(0.1)\n'
        '  result += 1\n'
    )

    def test___init__(self):
        connector = Connector(URL, None)
        self.assertTrue(connector.running)

    @httpretty.activate
    def test_terminate_on_error(self):
        httpretty.register_uri(httpretty.POST, "%s/pushcmd" % URL,
                               body=CMD_REPEAT, status=403, content_type=JSON)

        connector = Connector(URL, None)
        connector.run()  # catch error and return

    @httpretty.activate
    def test_retires_rest_prefix(self):
        httpretty.register_uri(httpretty.POST, "%s/pushcmd" % URL,
                               body=CMD_REPEAT, status=404, content_type=JSON)
        httpretty.register_uri(httpretty.POST, "%s/rest/pushcmd" % URL,
                               body=CMD_REPEAT, status=403, content_type=JSON)

        connector = Connector(URL, None)
        connector.run()  # catch error and return
        req = httpretty.last_request()
        self.assertEqual(req.path, '/rest/pushcmd')

    @httpretty.activate
    def test_sends_json_with_register(self):
        httpretty.register_uri(httpretty.POST, "%s/pushcmd" % URL,
                               body=CMD_REPEAT, status=403, content_type=JSON)

        connector = Connector(URL, None)
        connector.run()
        req = httpretty.last_request()
        self.assertEqual(req.headers['Content-Type'], JSON)
        body = httpretty.last_request().parsed_body
        self.assertEqual(body['cmd'], 'register')
        self.assertIn('token', body)
        self.assertIn('brickname', body)

    @httpretty.activate
    def test_register(self):
        responses = [
            httpretty.Response(body=CMD_REPEAT, status=200, content_type=JSON),
            httpretty.Response(body=CMD_REPEAT, status=403, content_type=JSON),
        ]
        httpretty.register_uri(httpretty.POST, "%s/pushcmd" % URL, responses=responses)

        connector = Connector(URL,  DummyService())
        connector.run()
        body = httpretty.last_request().parsed_body
        self.assertEqual(body['cmd'], 'push')
        self.assertIn('token', body)
        self.assertIn('brickname', body)

    def test_exec_good_code(self):
        connector = Connector(URL, None)
        res = connector._exec_code("test.py", TestConnector.GOOD_CODE, DummyAbortHandler())
        self.assertEqual(res, 0)

    def test_exec_bad_code(self):
        connector = Connector(URL, None)
        res = connector._exec_code("test.py", TestConnector.BAD_CODE, DummyAbortHandler())
        self.assertEqual(res, 1)

    def test_exec_code_with_result(self):
        connector = Connector(URL, None)
        res = connector._exec_code("test.py", TestConnector.GOOD_CODE_WITH_RESULT, DummyAbortHandler())
        self.assertEqual(res, 42)

    def test_exec_code_with_infinite_loop(self):
        connector = Connector(URL, None)
        with self.assertRaises(KeyboardInterrupt):
            connector._exec_code("test.py", TestConnector.INFINITE_LOOP, DummyAbortHandler(to_sleep=0.3))


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
