from __future__ import print_function
import pickle
import json
import math
import os.path
import calendar
import csv

from jira import JIRA
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, date, timedelta, timezone
from json import dumps

from rich.console import Console
from rich.table import Table
from rich import print

console = Console()

class TimeTracker():
    def __init__(self):
        creds = None
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)
        self.reload_settings()

        options = {"server": self.jira_settings["server"]}
        self.jira = JIRA(options, basic_auth=(self.jira_settings["username"], self.jira_settings["api_key"]))
       
        self.entry = None

    def reload_settings(self):
        with open('tasks.json') as file:
            j = json.load(file)
            self.tasks = j["tasks"]
            self.jira_settings = j["jira"]
            self.odoo_settings = j["odoo"]
            self.google_calendar = j["calendar"]

    def td_format(self, td_object):
        seconds = int(td_object.total_seconds())
        periods = [
            ('y', 60*60*24*365),
            ('m', 60*60*24*30),
            ('d', 60*60*24),
            ('h', 60*60),
            ('m', 60)
        ]

        strings=[]
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value , seconds = divmod(seconds, period_seconds)
                if period_name == "m" and seconds > 0:
                    period_value = period_value +1
                strings.append("%s%s" % (period_value, period_name))
        return " ".join(strings)

    def calculate_time_span(self, params):
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        begin_date = end_date = date.today()
        if params and len(params) > 0:
            if params[0] == "today":
                pass
            elif params[0] == "yesterday":
                begin_date = end_date = (begin_date + timedelta(days=-1))
            elif params[0] in months:
                (i, j) = calendar.monthrange(begin_date.year, months.index(params[0]) + 1)
                print(i,j)
                begin_date = date(year=begin_date.year, month=months.index(params[0]) + 1, day=1)
                end_date = date(year=begin_date.year, month=months.index(params[0]) + 1, day=j)
            elif "week" in params[0]:
                w = params[0][4:]
                d = "{}-W{}-1".format(begin_date.year, w)
                begin_date = datetime.strptime(d, "%Y-W%W-%w")
                print(begin_date)
                end_date = (begin_date + timedelta(days=7) + timedelta(minutes=-1))
                print(end_date)
            else:
                begin_date = end_date = datetime.strptime(params[0], '%Y%m%d')
               

        timeMin = datetime.combine(begin_date, datetime.min.time())
        timeMax = datetime.combine(end_date, datetime.max.time())
        return (timeMin, timeMax)

    def update_jira(self, params=None):
        page_token = None
        worklogs = []
        (timeMin, timeMax) = self.calculate_time_span(params)

        # print(timeMin, timeMax)
        
        while True:
            events = self.service.events().list(calendarId=self.google_calendar,
                                                timeMin=timeMin.isoformat()+'Z', timeMax=timeMax.isoformat()+'Z', pageToken=page_token).execute()

            for event in events['items']:
                # print(event)
                try:
                    start_datetime = datetime.strptime(event["start"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                    end_datetime = datetime.strptime(event["end"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                    span = math.ceil((end_datetime - start_datetime).total_seconds() / 60.0)
                    if not "description" in event.keys():
                         event["description"] = "."
                    worklogs.append({"issue": event["extendedProperties"]["private"]["jira"], "timeSpent": self.td_format(end_datetime - start_datetime), "comment": event["description"], "started": start_datetime})
                except:
                    pass
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        if worklogs != []:
            self.list_work_logs(worklogs)
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":
                for worklog in worklogs:
                    self.jira.add_worklog(worklog["issue"], comment=worklog["comment"], timeSpent=worklog["timeSpent"], started=worklog["started"])
                print("The work items have been synched with Jira")
        else:
            print("No work has been logged for the requested day")

    def jira_delete(self, params=None):
        worklogs = []
        worklogs_raw = []
       
        (timeMin, timeMax) = self.calculate_time_span(params)

        size = 100
        initial = 0
        while True:
            start = initial*size
            issues = self.jira.search_issues('project={} and assignee = currentUser()'.format(
                self.jira_settings["project_name"]), start, size)
            if len(issues) == 0:
                break
            initial += 1
            key = 1
            for issue in issues:
                for worklog in self.jira.worklogs(issue):
                   
                    worklog_started = datetime.strptime(
                       worklog.raw["started"], '%Y-%m-%dT%H:%M:%S.%f%z')
                    if timeMin.replace(tzinfo=timezone.utc) < worklog_started.replace(tzinfo=timezone.utc) < timeMax.replace(tzinfo=timezone.utc):
                        worklogs.append(worklog)
                        d = worklog.raw
                        d['issue'] = issue.raw['key']
                        worklogs_raw.append(d)
        
        if worklogs_raw != []:
            self.list_work_logs(worklogs_raw)
            console.print("JIRA worklogs listed above will be deleted. This action cannot be undone")
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":
                for worklog in worklogs:
                    worklog.delete()
                print("The work items have been deleted")


    def update_odoo(self, params=None):
        page_token = None
        worklogs = []
        if len(params) > 0:
            (timeMin, timeMax) = self.calculate_time_span(params)
        else:
            (timeMin, timeMax) = self.calculate_time_span(['today'])

        while True:
            events = self.service.events().list(calendarId=self.google_calendar, timeMin=timeMin, timeMax=timeMax, pageToken=page_token).execute()

            for event in events['items']:
                # print(event)
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
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        if worklogs != []:
            self.list_work_logs(worklogs)
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":
                with open('map.json') as file:
                    project_map = json.load(file)                
                with open('odoo.csv', 'w', newline='') as csvfile:
                    odoowriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    odoowriter.writerow(["id", "timesheet_ids/name", "timesheet_ids/account_id/id", "timesheet_ids/date", "timesheet_ids/unit_amount", "timesheet_ids/journal_id/id"])
                    time_sheet_id = "__export__.hr_timesheet_sheet_sheet_" + str(self.odoo_settings["time_sheet_id"])
                    for worklog in worklogs:
                        odoowriter.writerow([time_sheet_id, worklog["comment"], project_map[worklog["issue"]], worklog["started"],  worklog["timeSpent"], "hr_timesheet.analytic_journal"]) 
                        time_sheet_id = ""
                        

            print("The work items have been written to oddo.csv file.")
        else:
            print("No work has been logged for the requested day")       

    def list_work_logs(self, logs):
        table = Table(title="The following work items will be synched to Jira")
        table.add_column("Issue", style="cyan", no_wrap=True)
        table.add_column("Start Time", style="green")
        table.add_column("Summary", style="magenta")
        table.add_column("Time Spend", justify="right", style="green")
        for log in logs:
            table.add_row(log["issue"], str(log["started"]), log["comment"], log["timeSpent"])

        
        console.print(table, justify="left")

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

    def start(self, entry):
        self.entry = entry
        self.entry["start"] = {
                'dateTime': datetime.now().isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
        self.entry["end"] = {
                'dateTime': (datetime.now() + timedelta(minutes=30)).isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
        self.entry = self.service.events().insert(calendarId=self.google_calendar, body=self.entry).execute()

    def end(self):
        if self.entry != None:
            self.entry["end"] = {
                'dateTime': datetime.now().isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
            self.service.events().update(calendarId=self.google_calendar, eventId=self.entry['id'], body=self.entry).execute()
            self.entry = None

    def export_issues(self):
        size = 100
        initial = 0
        issues_dict = {}
        while True:
            start = initial*size
            issues = self.jira.search_issues('project=Swetree and assignee = currentUser()', start, size)
            if len(issues) == 0:
                break
            initial += 1
            key = 1
            for issue in issues:
                issues_dict[issue.key] = {"summary": issue.fields.summary,
                     "description": issue.fields.description,
                     "extendedProperties": {
                        "private": {
                            "jira": issue.key,
                            "project": "P4-18-4"
                            }
                    }

                }
        with open('export.json', 'w') as f:
            json.dump(issues_dict, f)

    def export_entries(self,  params=None):
        page_token = None
        entries = []
        (timeMin, timeMax) = self.calculate_time_span(params)
        print(timeMin, timeMax)
        while True:
            events = self.service.events().list(calendarId=self.google_calendar,
                                                timeMin=timeMin.isoformat()+'Z', timeMax=timeMax.isoformat()+'Z', pageToken=page_token).execute()
            for event in events['items']:
                entries.append(event)
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        with open('entries.json', 'w') as f:
            json.dump(entries, f)

    def update_entries(self,  params=None):
        with open('entries.json') as file:
            entries = json.load(file)
            for entry in entries:
                self.service.events().update(calendarId=self.google_calendar,
                                             eventId=entry['id'], body=entry).execute()



    def interactive(self):
        command = None
        while command != "exit":
            command = console.input(">>> ")
            commands = command.split()
            if commands[0] in self.tasks:
                self.end()
                self.start(self.tasks[commands[0]])
            elif commands[0] == "pause":
                self.end()
            elif commands[0] == "jira":
                self.update_jira(commands[1:])
            elif commands[0] == "odoo":
                self.update_odoo(commands[1:])
            elif commands[0] == "list":
                self.list_tasks(self.tasks)
            elif commands[0] == "export":
                self.export_issues()
            elif commands[0] == "j_delete":
                self.jira_delete(commands[1:])
            elif commands[0] == "g_export":
                self.export_entries(commands[1:])
            elif commands[0] == "g_update":
                self.update_entries(commands[1:])
            elif commands[0] == "reload":
                self.reload_settings()
        end()


if __name__ == '__main__':
    t = TimeTracker()
    # t.list_open_issues()
    t.interactive()
