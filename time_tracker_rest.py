from __future__ import print_function
import json

from gcalendar import GCalendar
from o365calendar import O365Calendar
from tracker_utils import *

import flask
from flask import Flask, session

app = Flask(__name__)
app.secret_key = "asdqweasd"
app.config["DEBUG"] = True

calendar = None

with open('settings.json') as file:
    settings = json.load(file)
    calendar = GCalendar(settings["google"])

@app.route('/tasks', methods=['GET'])
def tasks():
    with open('tasks.json') as file:
        j = json.load(file)
        tasks = j["tasks"]
        session["tasks"] = tasks
        return tasks


@app.route('/tasks/<string:task>', methods=['POST'])
def begin_task(task):
    print(task)
    if task in session["tasks"]:
        print(session["tasks"][task])
        calendar.end()
        calendar.start(session["tasks"][task])
    return ""

app.run()

