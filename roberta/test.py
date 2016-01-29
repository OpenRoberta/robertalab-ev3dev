# Hal class to satisfy testing


class Hal(object):

    def __init__(self, brickConfiguration, usedSensors):
        self.cfg = brickConfiguration
        self.usedSensors = usedSensors

    def clearDisplay(self):
        pass
