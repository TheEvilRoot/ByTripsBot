#!/usr/bin/env python3
import time
from datetime import datetime, timedelta
from os import environ as env

import telebot
from telebot.types import KeyboardButton as Kb
from telebot.types import ReplyKeyboardMarkup as Km

from i18n import default as ldef
from build import Build
from req import Req
from trip import Trip, VariantCompareResult

from threading import Thread

import requests as rq

TOKEN = env["TOKEN"]

bot = telebot.TeleBot(TOKEN)

update_thread = None

requests = {}
builds = {}

available_endpoints = [ldef["name.mogilev"], ldef["name.minsk"]]

origins_markup = Km()
origins_markup.add(*[Kb(f) for f in available_endpoints])

dates_markup = Km()
dates_markup.add(Kb(ldef["name.today"]), Kb(ldef["name.tomorrow"]))

confirm_markup = Km()
confirm_markup.add(Kb(ldef["name.confirm"]), Kb(ldef["name.date"]), Kb(ldef["name.origin"]))


def build_to_request(u, r):
    if u not in requests:
        requests[u] = []
    requests[u].append(r.req(u))
    builds.pop(u)
    return requests[u][-1]


def handle_date_answer(t):
    if t.lower() == ldef["name.today"].lower():
        return datetime.now()
    if t.lower() == ldef["name.tomorrow"].lower():
        return datetime.now() + timedelta(days=1)
    try:
        return datetime.strptime(t, "%d.%m.%Y")
    except ValueError:
        return None


def handle_confirm_answer(t):
    t = t.lower()
    if t == ldef["name.confirm"].lower():
        return True, None
    if t == ldef["name.date"].lower():
        return False, 'date'
    if t == ldef["name.origin"].lower():
        return False, 'origin'
    return False, None


def next_step(msg, u):
    if u not in builds or builds[u].date is None:
        step_get_date(msg)
    elif builds[u].origin is None:
        step_get_origin(msg)
    else:
        step_get_confirm(msg)


def update_build(u, **kwargs):
    if u not in builds:
        builds[u] = Build()
    builds[u].set(**kwargs)


def confirmation_message_for_build(build):
    return ldef["msg.confirm"].format(date=build.date.strftime("%d.%m.%Y"), origin=build.origin, dist=build.dist)


def step_get_date(msg):
    bot.send_message(msg.chat.id, ldef["msg.date.question"], reply_markup=dates_markup)
    bot.register_next_step_handler(msg, step_date)


def step_get_origin(msg):
    bot.send_message(msg.chat.id, ldef["msg.origin.question"], reply_markup=origins_markup)
    bot.register_next_step_handler(msg, step_origin)


def step_get_confirm(msg):
    bot.send_message(msg.chat.id, confirmation_message_for_build(builds[msg.chat.id]), reply_markup=confirm_markup)
    bot.register_next_step_handler(msg, step_confirm)


def step_add_request(msg, build):
    req = build_to_request(msg.chat.id, build)
    bot.send_message(msg.chat.id, ldef["msg.added.request"].format(route=req.route(), date=req.sdate))


def step_date(msg):
    d = handle_date_answer(msg.text)
    if d is None:
        bot.send_message(msg.chat.id, ldef["msg.date.invalid"])
        bot.register_next_step_handler(msg, step_date)
    else:
        bot.send_message(msg.chat.id, ldef["msg.date.selected"].format(date=d.strftime("%d.%m.%Y")))
        update_build(msg.chat.id, date=d)
        next_step(msg, msg.chat.id)


def step_origin(msg):
    bot.send_message(msg.chat.id, ldef["msg.origin.selected"].format(origin=msg.text))
    update_build(msg.chat.id, origin=msg.text)
    next_step(msg, msg.chat.id)


def step_confirm(msg):
    confirmed, field = handle_confirm_answer(msg.text)
    if confirmed:
        step_add_request(msg, builds[msg.chat.id])
    elif field is None:
        bot.send_message(msg.chat.id, ldef["msg.answer.invalid"])
        step_get_confirm(msg)
    else:
        update_build(msg.chat.id, **{field: None})
        next_step(msg, msg.chat.id)


@bot.message_handler(commands=['trips'])
def on_message(msg):
    next_step(msg, msg.chat.id)


def extract_dates(r):
    return set([s.sdate for s in r])


def request_trips_for_date(date):
    res = rq.get("http://avto-slava.by/timetable/trips/", data={'date': date})
    if res.status_code == 200:
        return res.json()['data']['trips']
    else:
        return None


def request_trips_for_dates(dates):
    data_per_date = {}
    for date in dates:
        data = request_trips_for_date(date)
        if data is None:
            print('Failed to request data for', date)
        data_per_date[date] = data
    return data_per_date


def message_for_compare_result(result):
    res, old, new = result
    if res == VariantCompareResult.NO_MORE_SEATS:
        return ldef["msg.result.no_seats"].format(name=new.short_name())
    elif res == VariantCompareResult.SEATS_SET_MORE:
        return ldef["msg.result.seats_set_more"].format(name=new.short_name(), old_seats=old.seats, new_seats=new.seats, all_seats=new.all_seats)
    elif res == VariantCompareResult.SEATS_SET_LESS:
        return ldef["msg.result.seats_set_less"].format(name=new.short_name(), old_seats=old.seats, new_seats=new.seats, all_seats=new.all_seats)


def invalidate_request(request):
    messages = []
    if request.data is not None:
        if len(request.data.trips) > 0:
            if request.cache is None:
                variants = '\n'.join(request.data.to_message([], only_with_seats=True))
                messages.append(f"{request.route()}\n{variants}")
            else:
                results = request.cache.compare(request.data)
                messages += [message_for_compare_result(result) for result in results]

        else:
            messages.append(ldef["msg.result.no_trips"].format(route=request.route()))
            requests[request.user].remove(request)
    else:
        messages.append(ldef["msg.result.error"].format(route=request.route()))
    for message in messages:
        bot.send_message(request.user, message)


def loop_iteration():
    if len(requests) > 0:
        all_requests = [req for reqs in requests.values() for req in reqs]
        data_per_date = request_trips_for_dates(extract_dates(all_requests))
        for (user, reqs) in requests.items():
            for request in reqs:
                data = data_per_date[request.sdate]
                request.cache = request.data
                request.data = Trip(request.route(), data)
                invalidate_request(request)


def looper():
    while True:
        loop_iteration()
        time.sleep(20)


def run_request_handler(thread):
    thread.start()


def run(thread):
    run_request_handler(thread)
    bot.polling()


if __name__ == '__main__':
    update_thread = Thread(target=looper)
    run(update_thread)
