from __future__ import print_function
import pickle
import json
import os.path


from rich.console import Console
from rich.table import Table
from rich import print

from gcalendar import GCalendar
from o365calendar import O365Calendar
from jira_handler import JiraHandler
from odoo_handler import OdooHandler
from tracker_utils import *

console = Console()

task_columns = [{"header": "Key", "field": "key", "style": "cyan", "no_wrap": True},
                {"header": "Description", "field": "summary", "style": "magenta"},
                {"header": "Project", "field": "extendedProperties.private.project", "justify": "right", "style": "green"},
                {"header": "Issue", "field": "extendedProperties.private.jira", "style": "cyan", "no_wrap": True} ]

class TimeTracker():
    def __init__(self):
        self.reload_settings()
        with open('settings.json') as file:
            self.settings = json.load(file)
        self.calendar = GCalendar(self.settings["google"])
        self.o365 = O365Calendar(self.settings["o365"])
        self.jira = JiraHandler(self.settings["jira"])
        self.odoo = OdooHandler(self.settings["odoo"])

    def reload_settings(self):
        with open('tasks.json') as file:
            j = json.load(file)
            self.tasks = j["tasks"]

    def help():
        pass

    def interactive(self):
        command = None
        while command != "exit":
            command = console.input(">>> ")
            commands = command.split()
            if commands[0] == "help":
                self.help()
            elif commands[0] in self.tasks:
                self.calendar.end()
                self.calendar.start(self.tasks[commands[0]])
                self.o365.end()
                self.o365.start(self.tasks[commands[0]])
            elif commands[0] == "pause":
                self.calendar.end()
                self.o365.end()
            elif commands[0] == "list":
                # self.list_tasks(self.tasks)
                t = self.tasks
                pretty_print(t, *task_columns)
            elif commands[0] == "elastic":
                events = self.calendar.fetch(*commands[1:])
                elastic(events)
            elif commands[0] == "jira":
                self.o365.fetch(*commands[1:])
                #events = self.calendar.fetch(*commands[1:])
                #self.jira.update(events)
            elif commands[0] == "odoo":
                events = self.calendar.fetch(*commands[1:])
                self.odoo.update(events)
            elif commands[0] == "j_export":
                self.jira.export_issues()
            elif commands[0] == "j_delete":
                self.jira.delete(*commands[1:])
            elif commands[0] == "g_export":
                self.calendar.export_entries(*commands[1:])
            elif commands[0] == "g_update":
                self.calendar.update_entries(*commands[1:])
            elif commands[0] == "reload":
                self.reload_settings()
        self.calendar.end()


if __name__ == '__main__':
    t = TimeTracker()
    t.interactive()
    # c = O365Calendar()
