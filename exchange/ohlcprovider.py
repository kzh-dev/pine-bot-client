# coding=utf-8

class BaseOHLCVProvider (object):

    def __init__ (self):
        self.barcount = 256

    def set_resolution (self, resolution):
        if resolution not in self.resolutions():
            raise Exception(f'unsupported resolution: {resolution}')
        self.resolution = resolution

    def set_barcount (self, barcount):
        self.barcount = barcount
