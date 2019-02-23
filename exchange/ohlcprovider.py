# coding=utf-8

class BaseOHLCVProvider (object):

    def set_resolution (self, resolution):
        if resolution not in self.resolutions():
            raise Exception(f'unsupported resolution: {resolution}')
        self.resolution = resolution

