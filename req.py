from datetime import datetime

class Req(object):
	def __init__(self, user, date, cfrom, dist):
		self.user = user
		self.date = date
		self.cfrom = cfrom
		self.dist = dist
		self.sdate = self.date.strftime("%Y-%m-%d")
		self.data = []
		self.status = None
		self.cache = []


