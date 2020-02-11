import requests as r
import time

def fetch_data(date):
	pass

def get_dates(requests): # -> [date]
	pass

def loop(requests, bot):
	while True:
		if len(requests) > 0:
			dates = {}
			invalidate = False
			req_dates = get_dates(requests)
			for date in req_dates:
				dates[date] = fetch_data(date)
				time.sleep(5)

			for req in requests:
				data = dates[req.sdate]
				route = f"{req.from.strip()} -> req.dist.strip()"
				data = [(key,d) for (key,d) in data if d["route"] == route]
				req.cache = req.data
				req.data = data
				if req.cache != req.data:
					req.status = "UPDATED"
					invalidate = True
				else:
					req.status = "NOUPDATES"
			if invalidate:
				notify_data_changed(bot, requests)
		time.sleep(30)
