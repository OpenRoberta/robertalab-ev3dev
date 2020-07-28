from .__version__ import version
import ctypes
import dbus
import dbus.service
from fcntl import ioctl
import json
import logging
import os
import socket
import stat
import struct
import time
import _thread
import threading
import urllib.request
import urllib.error
import urllib.parse
import sys

local_pkg_path = os.path.expanduser('~/.local/lib/python')
# ignore failure to make this testable outside of the target platform
try:
    from ev3dev import auto as ev3dev
    from .ev3 import Hal
except ImportError:
    from .test import Ev3dev as ev3dev
    from .test import Hal

logger = logging.getLogger('roberta.lab')

# configuration

# TRUE: use a new token per reconnect
# FALSE: try keep using the token for as long as possible
#        (needs robertalab > 1.4 or develop branch)
TOKEN_PER_SESSION = True


# helpers
def getHwAddr(ifname):
    # SIOCGIFHWADDR = 0x8927
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        info = ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
    return ':'.join(['%02x' % char for char in info[18:24]])


def generateToken():
    # note: we intentionally leave '01' and 'IO' out since they can be confused
    # when entering the code
    chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    # note: we don't use the random module since it is large
    b = os.urandom(8)
    return ''.join(chars[b[i] % len(chars)] for i in range(8))


def getBatteryVoltage():
    return "{0:.3f}".format(ev3dev.PowerSupply().measured_volts)


class Service(dbus.service.Object):
    """OpenRobertab-Lab dbus service

    The status state machine is as follows:

    +-> disconnected
    |   |
    |    v
    +- connected
    |    |
    |    v
    +- registered
    |    ^
    |    v
    +- executing

    """

    def __init__(self, path):
        logger.info('version: %s', version)
        logger.info('python path: %s', (':'.join(sys.path)))
        # passing None for path is only for testing
        if path:
            # needs /etc/dbus-1/system.d/openroberta.conf
            bus_name = dbus.service.BusName('org.openroberta.lab', bus=dbus.SystemBus())
            dbus.service.Object.__init__(self, bus_name, path)
            logger.debug('object registered')
            self.status('disconnected')
        self.hal = Hal(None)
        self.hal.clearDisplay()
        self.thread = None
        self.params = {
            'macaddr': '00:00:00:00:00:00',
            'firmwarename': 'ev3dev',
            'menuversion': version.split('-')[0],
        }
        self.updateConfiguration()

    def updateConfiguration(self):
        # or /etc/os-release
        with open('/proc/version', 'r') as ver:
            self.params['firmwareversion'] = ver.read()

        for iface in ['wlan', 'usb', 'eth']:
            for ix in range(10):
                try:
                    ifname = bytes(iface + str(ix), 'ascii')
                    self.params['macaddr'] = getHwAddr(ifname)
                    break
                except IOError:
                    pass
        # reusing token is nice for developers, but the server started to reject
        # them
        if not TOKEN_PER_SESSION:
            self.params['token'] = generateToken()

    @dbus.service.method('org.openroberta.lab', in_signature='s', out_signature='s')
    def connect(self, address):
        logger.debug('connect(%s)', address)
        if self.thread:
            logger.debug('disconnect() old thread')
            # make sure we don't change to disconnected when the thread
            # eventually terminates after the http timeout
            self.thread.service = None
            self.thread.running = False
        # start thread, connecting to address
        self.thread = Connector(address, self)
        self.thread.daemon = True
        self.thread.start()
        # TODO: we have to 'wait' until the connection has been established and
        # we got the token
        # - we could defer the "connected" signal and add another method to get
        #   the code
        self.status('connected')
        return self.thread.params['token']

    @dbus.service.method('org.openroberta.lab')
    def disconnect(self):
        logger.debug('disconnect()')
        self.thread.running = False
        self.status('disconnected')
        # end thread, can take up to 15 seconds (the timeout to return)
        # hence we don't join(), when connecting again we create a new thread
        # anyway
        # self.thread.join()
        # self.status('disconnected')
        self.thread = None

    @dbus.service.signal('org.openroberta.lab', signature='s')
    def status(self, status):
        logger.info('status changed: %s', status)


class GfxMode(object):

    def __init__(self):
        # get target vt from stdin, if vt number given by stdin is different than active vt number, we will have to switch then switch back
        self.tty_name = os.ttyname(sys.stdin.fileno())
        # get digit from string
        self.tty_num = int(list(filter(str.isdigit, self.tty_name))[0])
        try:
            # ugly hack to get current vt number, I didn't find any dbus properties to get it properly
            stream = os.popen('fgconsole')
            self.previous_tty_num = int(stream.readline())
            logger.info('current virtual terminal number is: %d', self.previous_tty_num)
        except:
            self.previous_tty_num = self.tty_num
            logger.exception('cannot read current virtual terminal number from fgconsole command, setting to %d', self.previous_tty_num)
        self.previous_tty_name = '/dev/tty' + str(self.previous_tty_num)
        try:
            bus = dbus.SystemBus()
            seat_obj = bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1/seat/seat0')
            self.seat_methods = dbus.Interface(seat_obj, 'org.freedesktop.login1.Seat')
        except:
            logger.exception('cannot open dbus interface for org.freedesktop.login1.Seat')

    def __enter__(self):
        # really useful ? Can block if permission is not set correctly on /dev/ttyx
        with open(self.tty_name, 'r') as tty:
            # KDSETMODE = 0x4B3A, GRAPHICS = 0x01
            ioctl(tty, 0x4B3A, 0x01)
        # change vt if not already done by caller
        if self.tty_name != self.previous_tty_num:
            logger.info('switching to tty: %s', self.tty_name)
            try:
                self.seat_methods.SwitchTo(self.tty_num)
            except:
                logger.exception('cannot switch to: %s', self.tty_name)

    def __exit__(self, type, value, traceback):
        # really useful ? Can block if permission is not set correctly on /dev/ttyx
        with open(self.tty_name, 'w') as tty:
            # KDSETMODE = 0x4B3A, TEXT = 0x00
            ioctl(tty, 0x4B3A, 0x00)
            # send Ctrl-L to tty to clear
            tty.write('\033c')
        # change vt if not managed by caller
        if self.tty_name != self.previous_tty_num:
            logger.info('switching back to tty: %s', self.previous_tty_name)
            try:
                self.seat_methods.SwitchTo(self.previous_tty_num)
            except:
                logger.exception('cannot switch back to: %s', self.previous_tty_name)


class AbortHandler(threading.Thread):
    """ Key press handler to abort running programms.
        Tests for a center+down press to soft-kill the programm or a 1 sec back
        key press and terminate the whole process"""

    def __init__(self, service, runner):
        threading.Thread.__init__(self)
        self.service = service
        self.running = True
        self.runner = runner

    def run(self):
        long_press = 0
        hal = self.service.hal
        while self.running:
            if hal.isKeyPressed('back'):
                logger.debug('back: %d', long_press)
                # if pressed for one sec, hard exit
                if long_press > 10:
                    logger.info('--- hard abort ---')
                    _thread.interrupt_main()  # throws KeyboardInterrupt
                    self.running = False
                    # something is eating the KeyboardInterrupt, this is a bit
                    # brute force, but works
                    os._exit(1)
                else:
                    long_press += 1
            elif hal.isKeyPressed('enter') and hal.isKeyPressed('down'):
                logger.debug('--- soft-abort ---')
                self.running = False
                self.ctype_async_raise(SystemExit)
            else:
                long_press = 0
            time.sleep(0.1)

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.running = False
        if type is not None:  # an exception has occurred
            logger.debug('Reraising exception: %s', str(type))
            return False      # reraise the exception
        else:
            logger.debug('No exception')
            return True

    def ctype_async_raise(self, exception):
        # adapted from https://gist.github.com/liuw/2407154
        found = False
        target_tid = 0
        for tid, tobj in list(threading._active.items()):
            if tobj is self.runner:
                found = True
                target_tid = tid
                break
        if not found:
            raise ValueError("Invalid thread object")

        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.py_object(exception))
        # ref: http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
        if ret == 0:
            raise ValueError("Invalid thread ID")
        elif ret > 1:
            # Huh? Why would we notify more than one threads?
            # Because we punch a hole into C level interpreter.
            # So it is better to clean up the mess.
            ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        logger.debug("Successfully set asynchronized exception for %d", target_tid)


class Connector(threading.Thread):
    """OpenRobertab-Lab network IO thread"""

    def __init__(self, address, service):
        threading.Thread.__init__(self)
        self.address = address.split('://', 1)[-1]  # stip protocol part
        self.service = service
        self.home = os.path.expanduser("~")
        if service:
            self.params = service.params
        else:
            self.params = {}
        if TOKEN_PER_SESSION:
            self.params['token'] = generateToken()

        self.registered = False
        self.running = True   # Used to cancel this through self.thread.running
        logger.debug('thread created')

    def _store_code(self, filename, code):
        # TODO: what can we do if the file can't be overwritten
        # https://github.com/OpenRoberta/robertalab-ev3dev/issues/26
        # - there is no point in catching if we only log it
        # - once we can report error details to the server, we can reconsider
        #   https://github.com/OpenRoberta/robertalab-ev3dev/issues/20
        with open(filename, 'w') as prog:
            # Apply hotfixes needed until server update
            # - the server generated code is python2 still
            code = code.replace('from __future__ import absolute_import\n', '')
            code = code.replace('in xrange(', 'in range(')
            code = code.replace('#!/usr/bin/python\n', '#!/usr/bin/python3\n')
            prog.write(code)
        os.chmod(filename, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)
        return code

    def _exec_code(self, filename, code, abort_handler):
        result = 0
        # using a new process would be using this, but is slower (4s vs <1s):
        # result = subprocess.call(["python", filename], env={"PYTHONPATH":"$PYTONPATH:."})
        # logger.info('execution result: %d' % result)
        #
        # NOTE: we don't have to keep pinging the server while running
        #   the code - robot is busy until we send push request again
        #   it would be nice though if we could cancel the running program
        try:
            compiled_code = compile(code, filename, 'exec')
            with abort_handler:
                scope = {
                    '__name__': '__main__',
                    'result': 0,
                }
                exec(compiled_code, scope)
                result = scope['result']
            logger.info('execution finished: result = %d', result)
        except KeyboardInterrupt:
            logger.info("reraise hard kill")
            raise
        except SystemExit:
            result = 143
            logger.info("soft kill")
        except:  # noqa: E722
            result = 1
            # TODO: return exception details as a string and put into a
            # 'nepoexitdetails' field, so that we can show this in the UI
            logger.exception("Ooops:")
        return result

    def _request(self, cmd, headers, timeout, send_params=True):
        protocol = 'https'
        url = '%s://%s/%s' % (protocol, self.address, cmd)
        while True:
            try:
                logger.debug('sending request to: %s', url)
                req = urllib.request.Request(url, headers=headers)
                data = None
                if send_params:
                    data = json.dumps(self.params).encode('utf8')
                    logger.debug('  with params: %s', data)
                return urllib.request.urlopen(req, data, timeout=timeout)
            except urllib.error.HTTPError as e:
                if e.code == 404 and '/rest/' not in url:
                    logger.warning("HTTPError(%s): %s, retrying with '/rest'", e.code, e.reason)
                    # upstream changed the server path
                    url = '%s://%s/rest/%s' % (protocol, self.address, cmd)
                elif e.code == 405 and protocol == 'https':
                    # TODO(ensonic): this only works for http->https
                    logger.warning("HTTPError(%s): %s, retrying with 'http://'", e.code, e.reason)
                    protocol = 'http'
                    url = "http" + url[5:]
                else:
                    logger.warning("HTTPError(%s): %s, unhandled!'", e.code, e.reason)
                    raise e
            except urllib.error.URLError as e:
                # [SSL: UNKNOWN_PROTOCOL] unknown protocol
                logger.warning("URLError(%s): %s, retrying with 'http://'", e.errno, e.reason)
                protocol = 'http'
                url = "http" + url[5:]
        return None

    def run(self):
        logger.debug('network thread started')
        # network related locals
        # TODO: change the user agent:
        # https://docs.python.org/2/library/urllib2.html#urllib2.Request
        # default is "Python-urllib/<version>"
        headers = {
            'Content-Type': 'application/json'
        }
        timeout = 15  # seconds

        logger.debug('target: %s', self.address)
        while self.running:
            if self.registered:
                self.params['cmd'] = 'push'
                timeout = 15
            else:
                self.params['cmd'] = 'register'
                timeout = 330
            self.params['brickname'] = socket.gethostname()
            self.params['battery'] = getBatteryVoltage()

            try:
                # TODO: according to https://tools.ietf.org/html/rfc6202
                # we should use keep alive
                # http://stackoverflow.com/questions/1037406/python-urllib2-with-keep-alive
                # http://stackoverflow.com/questions/13881196/remove-http-connection-header-python-urllib2
                # https://github.com/jcgregorio/httplib2
                response = self._request("pushcmd", headers, timeout)
                reply = json.loads(response.read().decode('utf8'))
                logger.debug('response: %s', json.dumps(reply))
                cmd = reply['cmd']
                if cmd == 'repeat':
                    if not self.registered:
                        self.service.status('registered')
                        self.service.hal.playFile(2)
                    self.registered = True
                    self.params['nepoexitvalue'] = 0
                elif cmd == 'abort':
                    # if service is None, the user canceled
                    if not self.registered and self.service:
                        logger.info('token collision, retrying')
                        self.params['token'] = generateToken()
                        # make sure we don't DOS the server
                        time.sleep(1.0)
                    else:
                        break
                elif cmd == 'download':
                    # TODO: url is not part of reply :/
                    # TODO: we should receive a digest for the download (md5sum) so that
                    #   we can verify the download
                    logger.debug('download code: %s/download', self.address)
                    response = self._request('download', headers, timeout)
                    hdr = response.getheader('Content-Disposition')
                    # save to $HOME/
                    filename = os.path.join(self.home, hdr.split('=')[1] if hdr else 'unknown')
                    code = self._store_code(filename, response.read().decode('utf-8'))
                    logger.info('code downloaded to: %s', filename)
                    # use a long-press of backspace to terminate
                    abort_handler = AbortHandler(self.service, self)
                    abort_handler.daemon = True
                    # This will make brickman switch vt
                    self.service.status('executing')
                    with GfxMode():
                        self.service.hal.clearDisplay()
                        self.params['nepoexitvalue'] = self._exec_code(filename, code, abort_handler)
                        # if the user did wait for a key press, wait for the key for be released
                        # before handing control back (to e.g. brickman)
                        while self.service.hal.isKeyPressed('any'):
                            time.sleep(0.1)
                        self.service.hal.resetState()
                    self.service.status('registered')
                elif cmd == 'update':
                    # import them here, since we don't use them otherwise
                    from io import BytesIO
                    import shutil
                    import zipfile

                    logger.info('download update: %s/update/ev3dev/runtime', self.address)
                    # fetch roberta.zip
                    response = self._request('update/ev3dev/runtime', headers, timeout, send_params=False)
                    zip_buf = BytesIO(response.read())
                    # remove the 'roberta' dir first and then recreate to make sure we don't accumulate files
                    shutil.rmtree(os.path.join(local_pkg_path, 'roberta'), ignore_errors=True)
                    # and unpack update
                    with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
                        zip_ref.extractall(local_pkg_path)
                    logger.info('firmware updated')
                    # then restart:
                    # TODO: maybe we can reuse the token (pass as arg)?
                    os.execl(sys.executable, sys.executable, *sys.argv)
                else:
                    logger.warning('unhandled command: %s', cmd)
            except urllib.error.HTTPError as e:
                # e.g. [Errno 404]
                retry = False

                # various server errors where we should just retry
                if 500 <= e.code <= 510:
                    retry = True

                if not retry:
                    logger.error("HTTPError(%s): %s", e.code, e.reason)
                    break
                else:
                    logger.error("HTTPError(%s): %s (retrying)", e.code, e.reason)
            except urllib.error.URLError as e:
                # e.g. [Errno 111] Connection refused
                #                  The handshake operation timed out
                # errors can be nested
                nested_e = None
                if len(e.args) > 0:
                    nested_e = e.args[0]
                elif e.__cause__:
                    nested_e = e.__cause__
                retry = False
                if nested_e:
                    # this happens if packets were lost
                    if isinstance(nested_e, socket.timeout):
                        retry = True
                    # this happens if we loose network
                    if isinstance(nested_e, socket.gaierror):
                        retry = True
                    if isinstance(nested_e, socket.herror):
                        retry = True
                    if isinstance(nested_e, socket.error):
                        retry = True
                else:
                    retry = True

                if not retry:
                    logger.error("URLError: %s: %s", self.address, e.reason)
                    logger.debug("URLError: %s", repr(e))
                    if nested_e:
                        logger.debug("Nested Exception: %s", repr(nested_e))
                    break
                else:
                    logger.info("URLError: %s: %s (retrying)", self.address, e.reason)
            except (socket.timeout, socket.gaierror, socket.herror, socket.error):
                pass
            except:  # noqa: E722
                logger.exception("Ooops:")
        logger.info('network thread stopped')
        if self.service:
            self.service.status('disconnected')
            # don't play if we we just canceled a registration
            if self.registered:
                self.service.hal.playFile(3)
