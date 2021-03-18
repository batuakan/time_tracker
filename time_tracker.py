from __future__ import print_function
import pickle
import json
import os.path


from rich.console import Console
from rich.table import Table
from rich import print

from gcalendar import GCalendar
from jira_handler import JiraHandler
from odoo_handler import OdooHandler
from tracker_utils import *

console = Console()

class TimeTracker():
    def __init__(self):
        self.reload_settings()
        with open('settings.json') as file:
            self.settings = json.load(file)
        self.calendar = GCalendar(self.settings["google"])
        self.jira = JiraHandler(self.settings["jira"])
        self.odoo = OdooHandler(self.settings["odoo"])

    def reload_settings(self):
        with open('tasks.json') as file:
            j = json.load(file)
            self.tasks = j["tasks"]

    def help():
        pass

    def list_tasks(self, tasks):
        table = Table(title="Tasks")
        table.add_column("Code", style="cyan", no_wrap=True)
        table.add_column("Summary", style="magenta")
        table.add_column("Project", style="green")
        for key in tasks.keys():
            try:
                table.add_row(key, tasks[key]["summary"], tasks[key]["extendedProperties"]["private"]["project"])
            except:
                pass
        console.print(table, justify="left")  

    def interactive(self):
        command = None
        while command != "exit":
            command = console.input(">>> ")
            commands = command.split()
            elif commands[0] == "help":
                self.help()
            if commands[0] in self.tasks:
                self.calendar.end()
                self.calendar.start(self.tasks[commands[0]])
            elif commands[0] == "pause":
                self.calendar.end()
            elif commands[0] == "list":
                self.list_tasks(self.tasks)
            elif commands[0] == "jira":
                events = self.calendar.fetch(*commands[1:])
                self.jira.update(events)
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
