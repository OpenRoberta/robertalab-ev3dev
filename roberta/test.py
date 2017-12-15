# Hal and Ev3dev class to satisfy testing

from PIL import Image, ImageDraw


class Hal(object):

    def __init__(self, brickConfiguration, usedSensors=None):
        self.cfg = brickConfiguration

    def clearDisplay(self):
        pass

    def playFile(self, systemSound):
        pass


class Ev3dev(object):
    OUTPUT_A = 'outA'
    OUTPUT_B = 'outB'
    OUTPUT_C = 'outC'
    OUTPUT_D = 'outD'

    INPUT_1 = 'in1'
    INPUT_2 = 'in2'
    INPUT_3 = 'in3'
    INPUT_4 = 'in4'

    class Leds(object):
        BLACK = 0
        GREEN = 1
        RED = 2
        ORANGE = 3
        LEFT = 4
        RIGHT = 5

    Sound = None

    def Button():
        return None

    class Screen(object):
        draw = None

        def __init__(self):
            im = Image.new('1', (178, 128), (0))
            self.draw = ImageDraw.Draw(im)

    class LargeMotor(object):

        def __init__(self, port):
            self.port = port
            self.position = 0
            self.state = False
            self.max_speed = 100
            self.count_per_rot = 360

        def run_to_rel_pos(self, **kwargs):
            self.args = kwargs

        def run_direct(self, **kwargs):
            self.args = kwargs
            # TODO: the calling code waits for the positions to be reached, we
            # only know the directions :/
            if kwargs['duty_cycle_sp'] >= 0:
                self.position = 10000
            else:
                self.position = -10000

        def stop(self):
            pass
