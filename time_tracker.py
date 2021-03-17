from __future__ import print_function
import pickle
import json
import time
import math
import os.path
import calendar
import csv

from jira import JIRA

from datetime import datetime, date, timedelta, timezone
import dateutil.parser

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

    def update_odoo(self, *args):
        page_token = None
        worklogs = []
        for event in self.calendar.fetch(*args):
            try:
                start_datetime = datetime.strptime(event["start"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                end_datetime = datetime.strptime(event["end"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                print(start_datetime, end_datetime)
                span_hours = (end_datetime - start_datetime).total_seconds() / 60.0 / 60.0
                if not "description" in event.keys():
                        event["description"] = ""
                comment = "{}-{} {} --- {}".format(start_datetime.time().strftime("%H:%M"), end_datetime.time().strftime("%H:%M"), event["summary"], event["description"])
                worklogs.append({"issue": event["extendedProperties"]["private"]["project"], "timeSpent": str(span_hours), "comment": comment, "started": start_datetime.date().strftime("%Y-%m-%d")})
            except:
                pass

        if worklogs != []:
            self.list_work_logs(worklogs)
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":            
                with open('odoo.csv', 'w', newline='') as csvfile:
                    odoowriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    odoowriter.writerow(["id", "timesheet_ids/name", "timesheet_ids/account_id/id", "timesheet_ids/date", "timesheet_ids/unit_amount", "timesheet_ids/journal_id/id"])
                    time_sheet_id = "__export__.hr_timesheet_sheet_sheet_" + str(self.odoo_settings["time_sheet_id"])
                    for worklog in worklogs:
                        odoowriter.writerow([time_sheet_id, worklog["comment"], self.odoo_settings["map"][worklog["issue"]],
                                             worklog["started"],  worklog["timeSpent"], "hr_timesheet.analytic_journal"])
                        time_sheet_id = ""
                        

            print("The work items have been written to oddo.csv file.")
        else:
            print("No work has been logged for the requested day")       

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
        # console = Console()
        console.print(table, justify="left")

    # def version_update(self, *args):
    #     entries = []
    #     for event in self.calendar.fetch(*args):    
    #         if 'extendedProperties' in event:
    #             if "version" not in event["extendedProperties"]["private"]:
    #                 event["extendedProperties"]["private"]["version"] = "0.0.1"
    #                 if "jira" in event["extendedProperties"]["private"]:
    #                     issue_id = event["extendedProperties"]["private"]["jira"]
    #                     event["extendedProperties"]["private"]["jira_issue_id"] = issue_id
    #                 if "project" in event["extendedProperties"]["private"]:
    #                     odoo_project = event["extendedProperties"]["private"]["project"]
    #                     event["extendedProperties"]["private"].pop(
    #                         'project', None)
    #                     event["extendedProperties"]["private"]["odoo_project"] = odoo_project
    #         entries.append(event)

    #     with open('entries.json', 'w') as f:
    #         json.dump(entries, f)   

    def interactive(self):
        command = None
        while command != "exit":
            command = console.input(">>> ")
            commands = command.split()
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
            # elif commands[0] == "v_update":
            #     self.version_update(*commands[1:])
            elif commands[0] == "reload":
                self.reload_settings()
        self.calendar.end()


if __name__ == '__main__':
    t = TimeTracker()
    t.interactive()
