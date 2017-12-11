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
