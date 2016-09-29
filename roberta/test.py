# Hal class to satisfy testing


class Hal(object):

    def __init__(self, brickConfiguration, usedSensors=None):
        self.cfg = brickConfiguration

    def clearDisplay(self):
        pass

    def playFile(self, systemSound):
        pass
