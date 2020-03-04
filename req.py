from datetime import datetime

from util import invert_origin
from i18n import default as ldef


class Req(object):
    def __init__(self, user, date, origin):
        self.user = user
        self.date = date
        self.origin = origin
        self.dist = invert_origin(origin, ldef["name.minsk"], ldef["name.mogilev"])
        self.sdate = self.date.strftime("%Y-%m-%d")
        self.data = None
        self.status = None
        self.cache = None

    def route(self):
        return f'{self.origin} -> {self.dist}'

    def __eq__(self, other):
        return other.route() == self.route() and other.sdate == self.sdate
