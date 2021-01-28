from __future__ import print_function
import pickle
import json
import math
import os.path
from jira import JIRA
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, date, timedelta
from json import dumps

from rich.console import Console
from rich.table import Table
from rich import print

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
        with open('tasks.json') as file:
            self.tasks = json.load(file)

        options = {"server": self.tasks["jira"]["server"]}
        self.jira = JIRA(options, basic_auth=(self.tasks["jira"]["username"], self.tasks["jira"]["api_key"]))
       
        self.entry = None

    def td_format(self, td_object):
        seconds = int(td_object.total_seconds())
        periods = [
            ('y', 60*60*24*365),
            ('m', 60*60*24*30),
            ('d', 60*60*24),
            ('h', 60*60),
            ('m', 60),
            ('s', 1)
        ]

        strings=[]
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value , seconds = divmod(seconds, period_seconds)
                strings.append("%s%s" % (period_value, period_name))

        return " ".join(strings)

    def update_jira(self, params=None):
        page_token = None
        worklogs = []
        filter_date = date.today()
        if len(params) > 0:
            if params[0] == "today":
                pass
            elif params[0] == "yesterday":
                filter_date = (filter_date + timedelta(days=-1))
            else:
                filter_date = datetime.strptime(params[0], '%Y%m%d')

        timeMin = datetime.combine(filter_date, datetime.min.time()).isoformat()+'Z'
        timeMax = datetime.combine(filter_date, datetime.max.time()).isoformat()+'Z'
        print(timeMin, timeMax)
        
        while True:
            events = self.service.events().list(calendarId=self.tasks["calendar"], timeMin=timeMin, timeMax=timeMax, pageToken=page_token).execute()

            for event in events['items']:
                # print(event)
                try:
                    start_datetime = datetime.strptime(event["start"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                    end_datetime = datetime.strptime(event["end"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                    span = math.ceil((end_datetime - start_datetime).total_seconds() / 60.0)
                    worklogs.append({"issue": event["extendedProperties"]["private"]["jira"], "timeSpent": self.td_format(end_datetime - start_datetime), "comment": event["summary"], "started": start_datetime})
                except:
                    pass
                #span = event["start"]["datetime"] - event["start"]["datetime"]
                #Get the issue tag and update it
                #jira.add_worklog("SWET-192", timeSpent="1m", comment="this is a test")

            page_token = events.get('nextPageToken')
            if not page_token:
                break
        if worklogs != []:
            self.list_work_logs(worklogs)
            s = input(">yes>no>")
            if s == "yes":
                for worklog in worklogs:
                    self.jira.add_worklog(worklog["issue"], comment=worklog["comment"], timeSpent=worklog["timeSpent"], started=worklog["started"])
                print("The work items have been synched with Jira")
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

        console = Console()
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
        console = Console()
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
        self.entry = self.service.events().insert(calendarId=self.tasks["calendar"], body=self.entry).execute()

    def end(self):
        if self.entry != None:
            self.entry["end"] = {
                'dateTime': datetime.now().isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
            self.service.events().update(calendarId=self.tasks["calendar"], eventId=self.entry['id'], body=self.entry).execute()
            self.entry = None

    def list_open_issues(self):
        size = 100
        initial = 0
        issues_dict = {}
        while True:
            start = initial*size
            issues = self.jira.search_issues('project=Swetree and assignee = currentUser() and status = "To Do"', start, size)
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
        

    def interactive(self):
        command = None
        while command != "exit":
            command = input(">>> ")
            commands = command.split()
            if commands[0] in self.tasks['tasks']:
                self.end()
                self.start(self.tasks['tasks'][commands[0]])
            if commands[0] == "pause":
                self.end()
            if commands[0] == "sync":
                self.update_jira(commands[1:])
            elif commands[0] == "list":
                self.list_tasks(self.tasks["tasks"])
                
        end()


if __name__ == '__main__':
    t = TimeTracker()
    # t.list_open_issues()
    t.interactive()
