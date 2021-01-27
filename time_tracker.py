from __future__ import print_function
import pickle
import json
import math
import os.path
from jira import JIRA
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, date
from json import dumps

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



    def update_jira(self, command=None):
        page_token = None
        entries = []
        while True:
            events = self.service.events().list(calendarId=self.tasks["calendar"], pageToken=page_token).execute()

            for event in events['items']:
                # print(event)
                try:
                    start_datetime = datetime.strptime(event["start"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                    end_datetime = datetime.strptime(event["end"]["dateTime"][:-6], '%Y-%m-%dT%H:%M:%S')
                    span = math.ceil((end_datetime - start_datetime).total_seconds() / 60.0)
                    entries.append({"issue": event["extendedProperties"]["private"]["jira"], "timeSpent": str(span) + "m", "comment": event["summary"], "started": start_datetime})
                except:
                    pass
                #span = event["start"]["datetime"] - event["start"]["datetime"]
                #Get the issue tag and update it
                #jira.add_worklog("SWET-192", timeSpent="1m", comment="this is a test")

            page_token = events.get('nextPageToken')
            if not page_token:
                break
        if entries != []:
            for entry in entries:
                print(entry)


    def start(self, entry):
        self.entry = self.tasks['tasks'][command]
        self.entry["start"] =  {
                'dateTime': datetime.now().isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
        pass

    def end(self):
        if self.entry != None:
            self.entry["end"] =  {
                'dateTime': datetime.now().isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
            self.entry = self.service.events().insert(calendarId=self.tasks["calendar"], body=self.entry).execute()

    def run(self):
        command = None
        while command != "exit":
            command = input(">>> ")
            if command in self.tasks['tasks']:
                self.end()
                self.start(self.tasks['tasks'][command])
            if command == "jira":
                self.update_jira()

if __name__ == '__main__':
    t = TimeTracker()
    t.run()