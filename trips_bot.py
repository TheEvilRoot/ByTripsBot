#!/usr/bin/env python3

import telebot
from telebot import types
from telebot.types import KeyboardButton as KB
from telebot.types import ReplyKeyboardMarkup as KM
from os import environ as env
from datetime import date, time, datetime, timedelta

from req import Req
from i18n import default as ldef

class Build(object):

	def __init__(self, date=None, cfrom=None, dist=None):
		self.date = date
		self.cfrom = cfrom
		self.dist = dist
	
	def req(u): 
		return Req(u, self.date, self.cfrom, self.dist) 

TOKEN = env["TOKEN"]

bot = telebot.TeleBot(TOKEN)

requests = {}
builds = {}

cities_markup = KM()
cities_markup.add(KB('Минск'), KB('Витебск'), KB('Могилев'), KB('Брест'), KB('Гродно'), KB('Гомель'))

dates_markup = KM()
dates_markup.add(KB('Today'), KB('Tomorrow'))

confirm_markup = KM()
confirm_markup.add(KB('Confirm'), KB('Date'), KB('From'), KB('To'))

def add_request(u, r):
	if u not in requests:
		requests[u] = []
	requests[u].append(Req(u, r['date'], r['from'], r['dist']))
	return requests[u][-1]

def handle_date(t):
	if t.lower() == 'today':
		return datetime.now()
	if t.lower() == 'tomorrow':
		return datetime.now() + timedelta(days=1)
	try:
		return datetime.strptime(t, "%d.%m.%Y")
	except:
		return None

def handle_confirm(t):
	t = t.lower()
	if t == 'confirm':
		return True, None
	if t == 'date':
		return False, 'date'
	if t == 'from':
		return False, 'from'
	if t == 'to':
		return False, 'dist'
	return False, None

def msg_for_build(build):
	return f'Your request:\nDate: {build["date"].strftime("%d.%m.%Y")}\nFrom: {build["from"]}\nTo: {build["dist"]}\nAll right or edit some field?'

def step_get_date(msg):
	bot.send_message(msg.chat.id, ldef["msg.date.question"], reply_markup=dates_markup)
	bot.register_next_step_handler(msg, step_date)	

def step_get_from(msg):
	bot.send_message(msg.chat.id, 'Now, select city your trip going from.', reply_markup=cities_markup)
	bot.register_next_step_handler(msg, step_from)

def step_get_dist(msg):
	bot.send_message(msg.chat.id, 'Now, select city your trip going to.', reply_markup=cities_markup)
	bot.register_next_step_handler(msg, step_dist)

def step_get_confirm(msg):
	bot.send_message(msg.chat.id, msg_for_build(builds[msg.chat.id]), reply_markup=confirm_markup)
	bot.register_next_step_handler(msg, step_confirm)

def step_get_trips(msg, build):
	req = add_request(msg.chat.id, build)
	bot.send_message(msg.chat.id, f'Your request {req.cfrom} -> {req.dist} {req.sdate} added, wait for updates!')

def next_step(msg, u):
	if u not in builds or builds[u]['date'] is None:
		step_get_date(msg)
	elif builds[u]['from'] is None:
		step_get_from(msg)
	elif builds[u]['dist'] is None:
		step_get_dist(msg)
	else:
		step_get_confirm(msg)

def set_build(u, cfrom=None, dist=None, date=None):
	if cfrom is None and dist is None and date is None:
		return
	if u not in builds:
		builds[u] = {'date': date, 'from': cfrom, 'dist': dist}
	else:
		if cfrom is not None:
			builds[u]['from'] = cfrom
		if dist is not None:
			builds[u]['dist'] = dist
		if date is not None:
			builds[u]['date'] = date

def step_date(msg):	
	d = handle_date(msg.text)
	if d is None:
		bot.send_message(msg.chat.id, ldef["msg.date.invalid"])
		bot.register_next_step_handler(msg, step_date)	
	else:	
		bot.send_message(msg.chat.id, ldef["msg.date.selected"].format(d.strftime("%d.%m.%Y")))
		set_build(msg.chat.id, date=d)
		next_step(msg, msg.chat.id)

def step_from(msg):
	bot.send_message(msg.chat.id, ldef["msg.origin.selected"].format(msg.text))
	set_build(msg.chat.id, cfrom=msg.text)
	next_step(msg, msg.chat.id)

def step_dist(msg):
	bot.send_message(msg.chat.id, ldef["msg.dist.selected"].fotmat(msg.text))
	set_build(msg.chat.id, dist=msg.text)
	next_step(msg, msg.chat.id)

def step_confirm(msg):
	confirmed, field = handle_confirm(msg.text)
	if confirmed:
		build = builds.pop(msg.chat.id)
		step_get_trips(msg, build)
	elif field is None:
		bot.send_message(msg.chat.id,ldef["msg.answer.invalid"]) 
		step_get_confirm(msg)
	else:
		builds[msg.chat.id][field] = None
		next_step(msg, msg.chat.id)

@bot.message_handler(commands=['trips'])
def on_message(msg):
	next_step(msg,msg.chat.id)

def run():	
	bot.polling()

if __name__ == '__main__':
	run()
