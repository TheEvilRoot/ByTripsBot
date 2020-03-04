from req import Req
from util import invert_origin
from i18n import default as ldef


class Build(object):

    def __init__(self, date=None, origin=None):
        self.date = date
        self.origin = origin
        self.dist = invert_origin(origin, ldef["name.minsk"], ldef["name.mogilev"])

    def set(self, **kwargs):
        for (arg, value) in kwargs.items():
            if arg == "date":
                self.date = value
            elif arg == "origin":
                self.origin = value
                self.dist = invert_origin(value, ldef["name.minsk"], ldef["name.mogilev"])

    def req(self, u):
        return Req(u, self.date, self.origin)
