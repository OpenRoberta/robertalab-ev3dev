
from PIL import Image, ImageFont
import dbus
import glob
import logging
import math
import os
import re
import socket
import time

from ev3dev import auto as ev3dev
from roberta.StaticData import IMAGES

logger = logging.getLogger('roberta.ev3')


class Bluetooth:

    @staticmethod
    def getAddr(self, iface):
        try:
            with open('/sys/class/bluetooth/%s/address' % iface, 'r') as f:
                mac = f.read()
        except (AttributeError, OSError):
            logger.warning('no bluetooth device %s found', iface)
            mac = None
        return mac

    @staticmethod
    def isValidAddr(self, mac):
        if not mac:
            return False
        if not re.match(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', mac):
            return False
        return True


class Hal(object):

    # usedSensors is unused, the code-generator for lab.openroberta > 1.4 wont
    # pass it anymore
    def __init__(self, brickConfiguration, usedSensors=None):
        self.cfg = brickConfiguration
        dir = os.path.dirname(__file__)
        self.font_s = ImageFont.load(os.path.join(dir, 'ter-u12n_unicode.pil'))
        self.font_x = ImageFont.load(os.path.join(dir, 'ter-u18n_unicode.pil'))
        self.lcd = ev3dev.Screen()
        self.led = ev3dev.Leds
        self.keys = ev3dev.Button()
        self.sound = ev3dev.Sound
        (self.font_w, self.font_h) = self.lcd.draw.textsize('X', font=self.font_s)
        self.timers = {}
        self.images = {}
        self.sys_bus = None
        self.bt_server = None
        self.bt_connections = []

    @staticmethod
    def makeLargeMotor(port, regulated, direction, side):
        try:
            m = ev3dev.LargeMotor(port)
            m.speed_regulation_enabled = regulated
            if direction is 'backward':
                m.polarity = 'inversed'
            else:
                m.polarity = 'normal'
            m.cfg_side = side
            m.last_position = m.position
        except (AttributeError, OSError):
            logger.info('no large motor connected to port [%s]' % port)
            m = None
        return m

    @staticmethod
    def makeMediumMotor(port, regulated, direction, side):
        try:
            m = ev3dev.MediumMotor(port)
            m.speed_regulation_enabled = regulated
            if direction is 'backward':
                m.polarity = 'inversed'
            else:
                m.polarity = 'normal'
            m.cfg_side = side
            m.last_position = m.position
        except (AttributeError, OSError):
            logger.info('no medium motor connected to port [%s]' % port)
            m = None
        return m

    @staticmethod
    def makeColorSensor(port):
        try:
            s = ev3dev.ColorSensor(port)
        except (AttributeError, OSError):
            logger.info('no color sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeGyroSensor(port):
        try:
            s = ev3dev.GyroSensor(port)
        except (AttributeError, OSError):
            logger.info('no gyro sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeI2cSensor(port):
        try:
            s = ev3dev.I2cSensor(port)
        except (AttributeError, OSError):
            logger.info('no i2c sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeInfraredSensor(port):
        try:
            s = ev3dev.InfraredSensor(port)
        except (AttributeError, OSError):
            logger.info('no infrared sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeLightSensor(port):
        try:
            s = ev3dev.LightSensor(port)
        except (AttributeError, OSError):
            logger.info('no light sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeSoundSensor(port):
        try:
            s = ev3dev.SoundSensor(port)
        except (AttributeError, OSError):
            logger.info('no sound sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeTouchSensor(port):
        try:
            s = ev3dev.TouchSensor(port)
        except (AttributeError, OSError):
            logger.info('no touch sensor connected to port [%s]' % port)
            s = None
        return s

    @staticmethod
    def makeUltrasonicSensor(port):
        try:
            s = ev3dev.UltrasonicSensor(port)
        except (AttributeError, OSError):
            logger.info('no ultrasonic sensor connected to port [%s]' % port)
            s = None
        return s

    # control
    def waitFor(self, ms):
        time.sleep(ms / 1000.0)

    def busyWait(self):
        '''Used as interrupptible busy wait.'''
        time.sleep(0.0)

    # lcd
    def drawText(self, msg, x, y, font=None):
        font = font or self.font_s
        self.lcd.draw.text((x*self.font_w, y*self.font_h), msg, font=font)
        self.lcd.update()

    def drawPicture(self, picture, x, y):
        if picture not in self.images:
            self.images[picture] = Image.frombytes('1', (178, 128),
                                                   IMAGES[picture],
                                                   'raw', '1;IR', 0, 1)
        # FIXME: this should not poke into a private field
        # https://github.com/rhempel/ev3dev-lang-python/issues/142
        self.lcd._img.paste(self.images[picture], (x, y))
        self.lcd.update()

    def clearDisplay(self):
        self.lcd.clear()
        self.lcd.update()

    # led
    def ledOn(self, color, mode):
        # color: green, red, orange - LED.COLOR.{RED,GREEN,AMBER}
        # mode: on, flash, double_flash
        if mode is 'on':
            if color is 'green':
                self.led.set_color(ev3dev.Leds.LEFT, ev3dev.Leds.GREEN)
                self.led.set_color(ev3dev.Leds.RIGHT, ev3dev.Leds.GREEN)
            elif color is 'red':
                self.led.set_color(ev3dev.Leds.LEFT, ev3dev.Leds.RED)
                self.led.set_color(ev3dev.Leds.RIGHT, ev3dev.Leds.RED)
            elif color is 'orange':
                self.led.set_color(ev3dev.Leds.LEFT, ev3dev.Leds.ORANGE)
                self.led.set_color(ev3dev.Leds.RIGHT, ev3dev.Leds.ORANGE)
        elif mode in ['flash', 'double_flash']:
            # FIXME: timer mode does not support double flash
            group = []
            if color in ['green', 'orange']:
                group.append(self.led.green_left)
                group.append(self.led.green_right)
            if color in ['red', 'orange']:
                group.append(self.led.red_left)
                group.append(self.led.red_right)
            self.led.set(group, trigger='timer')
            # when the trigger attribute is set other attributes appear
            # dynamically :/ - but this still does not help :/
            for i in range(5):
                try:
                    self.led.set(group, delay_on=200, delay_off=800)
                    break
                except IOError as e:
                    logger.info('failed to set blink timing [%s]' % e.message)
                time.sleep(0.1)

    def ledOff(self):
        self.led.all_off()

    def resetLED(self):
        self.ledOff()

    # key
    def isKeyPressed(self, key):
        if key in ['any', '*']:
            return self.keys.any()
        else:
            # remap some keys
            key_aliases = {
                'escape':  'backspace',
                'back': 'backspace',
            }
            if key in key_aliases:
                key = key_aliases[key]
            return key in self.keys.buttons_pressed

    def isKeyPressedAndReleased(self, key):
        return False

    # tones
    def playTone(self, frequency, duration):
        frequency = frequency if frequency >= 100 else 0
        self.sound.tone(frequency, duration).wait()

    def playFile(self, systemSound):
        # systemSound is a enum for preset beeps:
        # http://www.lejos.org/ev3/docs/lejos/hardware/Audio.html#systemSound-int-
        # http://sf.net/p/lejos/ev3/code/ci/master/tree/ev3classes/src/lejos/remote/nxt/RemoteNXTAudio.java#l20
        C2 = 523
        if systemSound == 0:
            self.playTone(600, 200)
        elif systemSound == 1:
            self.sound.tone([(600, 150, 50), (600, 150, 50)]).wait()
        elif systemSound == 2:  # C major arpeggio
            self.sound.tone([(C2 * i / 4, 50, 50) for i in range(4, 7)]).wait()
        elif systemSound == 3:
            self.sound.tone([(C2 * i / 4, 50, 50) for i in range(7, 4, -1)]).wait()
        elif systemSound == 4:
            self.playTone(100, 500)

    def setVolume(self, volume):
        self.sound.volume = volume

    def getVolume(self):
        return self.sound.volume

    # actors
    # http://www.ev3dev.org/docs/drivers/tacho-motor-class/
    def rotateRegulatedMotor(self, port, speed_pct, mode, value):
        # mode: degree, rotations, distance
        speed_pct *= 10.0
        m = self.cfg['actors'][port]
        if mode is 'degree':
            m.run_to_rel_pos(speed_regulation_enabled='on', position_sp=value, speed_sp=int(speed_pct))
            while (m.state):
                self.busyWait()
        elif mode is 'rotations':
            value *= m.count_per_rot
            m.run_to_rel_pos(speed_regulation_enabled='on', position_sp=int(value), speed_sp=int(speed_pct))
            while (m.state):
                self.busyWait()

    def rotateUnregulatedMotor(self, port, speed_pct, mode, value):
        speed_pct *= 10.0
        m = self.cfg['actors'][port]
        if mode is 'rotations':
            value *= m.count_per_rot
        if speed_pct >= 0:
            value = m.position + value
            m.run_direct(duty_cycle_sp=int(speed_pct))
            while (m.position < value):
                self.busyWait()
        else:
            value = m.position - value
            m.run_direct(duty_cycle_sp=int(speed_pct))
            while (m.position > value):
                self.busyWait()
        m.stop()

    def turnOnRegulatedMotor(self, port, value):
        value *= 10.0
        self.cfg['actors'][port].run_forever(speed_regulation_enabled='on', speed_sp=int(value))

    def turnOnUnregulatedMotor(self, port, value):
        value *= 10.0
        self.cfg['actors'][port].run_direct(duty_cycle_sp=int(value))

    def setRegulatedMotorSpeed(self, port, value):
        value *= 10.0
        m = self.cfg['actors'][port]
        if m.state:
            m.run_forever(speed_regulation_enabled='on', speed_sp=int(value))
        else:
            m.speed_sp = 300

    def setUnregulatedMotorSpeed(self, port, value):
        value *= 10.0
        self.cfg['actors'][port].duty_cycle_sp = int(value)

    def getRegulatedMotorSpeed(self, port):
        return self.cfg['actors'][port].speed / 10.0

    def getUnregulatedMotorSpeed(self, port):
        return self.cfg['actors'][port].duty_cycle / 10.0

    def stopMotor(self, port, mode='float'):
        # mode: float, nonfloat
        # stop_commands: ['brake', 'coast', 'hold']
        m = self.cfg['actors'][port]
        if mode is 'float':
            m.stop_command = 'coast'
        elif mode is 'nonfloat':
            m.stop_command = 'brake'
        self.cfg['actors'][port].stop()

    def stopMotors(self, left_port, right_port):
        self.stopMotor(left_port)
        self.stopMotor(right_port)

    def stopAllMotors(self):
        # [m for m in [Motor(port) for port in ['outA', 'outB', 'outC', 'outD']] if m.connected]
        for file in glob.glob('/sys/class/tacho-motor/motor*/command'):
            with open(file, 'w') as f:
                f.write('stop')

    def regulatedDrive(self, left_port, right_port, reverse, direction, speed_pct):
        # direction: forward, backward
        # reverse: always false for now
        speed_pct *= 10.0
        if direction is 'backward':
            speed_pct = -speed_pct
        self.cfg['actors'][left_port].run_forever(speed_regulation_enabled='on',
                                                  speed_sp=int(speed_pct))
        self.cfg['actors'][right_port].run_forever(speed_regulation_enabled='on',
                                                   speed_sp=int(speed_pct))

    def driveDistance(self, left_port, right_port, reverse, direction, speed_pct, distance):
        # direction: forward, backward
        # reverse: always false for now
        speed_pct *= 10.0
        ml = self.cfg['actors'][left_port]
        mr = self.cfg['actors'][right_port]
        circ = math.pi * self.cfg['wheel-diameter']
        dc = distance / circ
        if direction is 'backward':
            dc = -dc
        # set all attributes
        ml.speed_regulation_enabled = 'on'
        ml.stop_command = 'brake'
        ml.position_sp = int(dc * ml.count_per_rot)
        ml.speed_sp = int(speed_pct)
        mr.speed_regulation_enabled = 'on'
        mr.stop_command = 'brake'
        mr.position_sp = int(dc * mr.count_per_rot)
        mr.speed_sp = int(speed_pct)
        # start motors
        ml.run_to_rel_pos()
        mr.run_to_rel_pos()
        # logger.debug("driving: %s, %s" % (ml.state, mr.state))
        while (ml.state or mr.state):
            self.busyWait()

    def rotateDirectionRegulated(self, left_port, right_port, reverse, direction, speed_pct):
        # direction: left, right
        # reverse: always false for now
        speed_pct *= 10.0
        if direction is 'left':
            self.cfg['actors'][right_port].run_forever(speed_regulation_enabled='on',
                                                       speed_sp=int(speed_pct))
            self.cfg['actors'][left_port].run_forever(speed_regulation_enabled='on',
                                                      speed_sp=int(-speed_pct))
        else:
            self.cfg['actors'][left_port].run_forever(speed_regulation_enabled='on',
                                                      speed_sp=int(speed_pct))
            self.cfg['actors'][right_port].run_forever(speed_regulation_enabled='on',
                                                       speed_sp=int(-speed_pct))

    def rotateDirectionAngle(self, left_port, right_port, reverse, direction, speed_pct, angle):
        # direction: left, right
        # reverse: always false for now
        speed_pct *= 10.0
        ml = self.cfg['actors'][left_port]
        mr = self.cfg['actors'][right_port]
        circ = math.pi * self.cfg['track-width']
        distance = angle * circ / 360.0
        circ = math.pi * self.cfg['wheel-diameter']
        dc = distance / circ
        logger.debug("doing %lf rotations" % dc)
        # set all attributes
        ml.speed_regulation_enabled = 'on'
        ml.stop_command = 'brake'
        ml.speed_sp = int(speed_pct)
        mr.speed_regulation_enabled = 'on'
        mr.stop_command = 'brake'
        mr.speed_sp = int(speed_pct)
        if direction is 'left':
            mr.position_sp = int(dc * mr.count_per_rot)
            ml.position_sp = int(-dc * ml.count_per_rot)
        else:
            ml.position_sp = int(dc * ml.count_per_rot)
            mr.position_sp = int(-dc * mr.count_per_rot)
        # start motors
        ml.run_to_rel_pos()
        mr.run_to_rel_pos()
        logger.debug("turning: %s, %s" % (ml.state, mr.state))
        while (ml.state or mr.state):
            self.busyWait()

    def driveInCurve(self, direction, left_port, left_speed_pct, right_port, right_speed_pct, distance=None):
        # direction: foreward, backwards
        left_speed_pct *= 10.0
        right_speed_pct *= 10.0
        ml = self.cfg['actors'][left_port]
        mr = self.cfg['actors'][right_port]
        if distance:
            speed_pct = (left_speed_pct + right_speed_pct) / 2.0
            circ = math.pi * self.cfg['wheel-diameter']
            dc = distance / circ
            left_dc = dc * left_speed_pct / speed_pct
            right_dc = dc * right_speed_pct / speed_pct
            # set all attributes
            ml.speed_regulation_enabled = 'on'
            ml.stop_command = 'brake'
            ml.speed_sp = int(left_speed_pct)
            mr.speed_regulation_enabled = 'on'
            mr.stop_command = 'brake'
            mr.speed_sp = int(right_speed_pct)
            if direction is 'backwards':
                ml.position_sp = int(-left_dc * ml.count_per_rot)
                mr.position_sp = int(-right_dc * mr.count_per_rot)
            else:
                ml.position_sp = int(left_dc * ml.count_per_rot)
                mr.position_sp = int(right_dc * mr.count_per_rot)
            # start motors
            ml.run_to_rel_pos()
            mr.run_to_rel_pos()
            while (ml.state or mr.state):
                self.busyWait()
        else:
            if direction is 'backwards':
                ml.run_forever(speed_regulation_enabled='on', speed_sp=int(-left_speed_pct))
                mr.run_forever(speed_regulation_enabled='on', speed_sp=int(-right_speed_pct))
            else:
                ml.run_forever(speed_regulation_enabled='on', speed_sp=int(left_speed_pct))
                mr.run_forever(speed_regulation_enabled='on', speed_sp=int(right_speed_pct))

    # sensors
    def scaledValue(self, sensor):
        return sensor.value() / (10.0 ** sensor.decimals)

    # touch sensor
    def isPressed(self, port):
        return self.scaledValue(self.cfg['sensors'][port])

    # ultrasonic sensor
    def getUltraSonicSensorDistance(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'US-DIST-CM'
        return self.scaledValue(s)

    def getUltraSonicSensorPresence(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'US-SI-CM'
        return self.scaledValue(s)

    # gyro
    # http://www.ev3dev.org/docs/sensors/lego-ev3-gyro-sensor/
    def resetGyroSensor(self, port):
        # change mode to reset for GYRO-ANG and GYRO-G&A
        self.cfg['sensors'][port].mode = 'GYRO-RATE'
        self.cfg['sensors'][port].mode = 'GYRO-ANG'

    def getGyroSensorValue(self, port, mode):
        # mode = rate, angle
        s = self.cfg['sensors'][port]
        if mode is 'angle':
            s.mode = 'GYRO-ANG'
        elif mode is 'rate':
            s.mode = 'GYRO-RATE'
        return self.scaledValue(s)

    # color
    # http://www.ev3dev.org/docs/sensors/lego-ev3-color-sensor/
    def getColorSensorAmbient(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'COL-AMBIENT'
        return self.scaledValue(s)

    def getColorSensorColour(self, port):
        colors = ['none', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown']
        s = self.cfg['sensors'][port]
        s.mode = 'COL-COLOR'
        return colors[int(self.scaledValue(s))]

    def getColorSensorRed(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'COL-REFLECT'
        return self.scaledValue(s)

    def getColorSensorRgb(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'RGB-RAW'
        return (s.value(0), s.value(1), s.value(2))

    # infrared
    # http://www.ev3dev.org/docs/sensors/lego-ev3-infrared-sensor/
    def getInfraredSensorSeek(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'IR-SEEK'
        return self.scaledValue(s)

    def getInfraredSensorDistance(self, port):
        s = self.cfg['sensors'][port]
        s.mode = 'IR-PROX'
        return self.scaledValue(s)

    # timer
    def getTimerValue(self, timer):
        if timer in self.timers:
            return time.clock() - self.timers[timer]
        else:
            self.timers[timer] = time.clock()

    def resetTimer(self, timer):
        del self.timers[timer]

    # tacho-motor position
    def resetMotorTacho(self, actorPort):
        m = self.cfg['actors'][actorPort]
        m.last_position = m.position

    def getMotorTachoValue(self, actorPort, mode):
        m = self.cfg['actors'][actorPort]
        tachoCount = m.position - m.last_position

        if mode == 'degree':
            return tachoCount * 360.0 / float(m.count_per_rot)
        elif mode in ['rotation', 'distance']:
            rotations = float(tachoCount) / float(m.count_per_rot)
            if mode == 'rotation':
                return rotations
            else:
                distance = round(math.pi * self.cfg['wheel-diameter'] * rotations)
                return distance
        else:
            raise ValueError('incorrect MotorTachoMode: %s' % mode)

    # communication
    def establishConnectionTo(self, host):
        # host can also be a name, resolving it is slow though and requires the
        # device to be visible
        if not Bluetooth.isValidAddr(host):
            #nearby_devices = bluetooth.discover_devices()
            #for bdaddr in nearby_devices:
            #    if host == bluetooth.lookup_name(bdaddr):
            #        host = bdaddr
            #        break
            logger.warning('no bluetooth discovery available')
            return -1
        if Bluetooth.isValidAddr(host):
            con = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            con.connect((host, 0))
            self.bt_connections.append(con)
            return len(self.bt_connections) - 1
        else:
            return -1

    def waitForConnection(self):
        # enable visibility
        if not self.sys_bus:
            self.sys_bus = dbus.SystemBus()
        # do only once (since we turn off the timeout)
        # alternatively set DiscoverableTimeout = 0 in /etc/bluetooth/main.conf
        # and run hciconfig hci0 piscan, from robertalab initscript
        hci0 = self.sys_bus.get_object('org.bluez', '/org/bluez/hci0')
        props = dbus.Interface(hci0, 'org.freedesktop.DBus.Properties')
        props.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(0))
        props.Set('org.bluez.Adapter1', 'Discoverable', True)

        if not self.bt_server:
            mac = Bluetooth.getAddr('hci0')
            if Bluetooth.isValidAddr(mac):
                con = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                con.bind((mac, 0))
                con.listen(1)
                self.bt_server = con

        (con, info) = self.bt_server.accept()
        self.bt_connections.append(con)
        return len(self.bt_connections) - 1

    def readMessage(self, con_ix):
        message = "NO MESSAGE"
        if con_ix < len(self.bt_connections) and self.bt_connections[con_ix]:
            logger.debug('reading msg')
            message = self.bt_connections[con_ix].recv(1024)
            logger.debug('received msg [%s]' % message)
        return message

    def sendMessage(self, con_ix, message):
        if con_ix < len(self.bt_connections) and self.bt_connections[con_ix]:
            logger.debug('sending msg [%s]' % message)
            self.bt_connection[con_ix].send(message)
            logger.debug('sent msg')
