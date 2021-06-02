
from __future__ import print_function
import pickle
import json

import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime, timedelta
import time as t
from tracker_utils import *

class GCalendar():
    def __init__(self, settings):
        self.settings = settings
        creds = None
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        if os.path.exists('tokens/token.pickle'):
            with open('tokens/token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'tokens/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('tokens/token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('calendar', 'v3', credentials=creds)
        self.entry = None

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
        self.entry = self.insert(self.entry)

    def end(self):
        if self.entry != None:
            self.entry["end"] = {
                'dateTime': datetime.now().isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
            # print(self.entry)
            self.update(self.entry)
            self.entry = None

    def fetch(self, *args):
        page_token = None
        timeMin, timeMax = calculate_time_span(*args)
        while True:
            page_events = self.service.events().list(calendarId=self.settings["calendar_id"], timeMin=timeMin.isoformat()+'Z', 
                          timeMax=timeMax.isoformat()+'Z', pageToken=page_token).execute()
            # events = events + page_events['items']
            for event in page_events['items']:
                yield event
            page_token = page_events.get('nextPageToken')
            if not page_token:
                break

    def export_entries(self,  *args):
        entries = []
        for event in self.fetch(*args):
            if "Lunch" not in event["summary"] and "extendedProperties" not in event:
                entries.append(event)
        with open('entries.json', 'w') as f:
            json.dump(entries, f)

    def update_entries(self,  *args):
        count = 0
        with open('entries.json') as file:
            entries = json.load(file)
            print("Number of items to be updated: {}".format(len(entries)))
            try:
                for entry in entries:
                    self.update(entry)
                    count = count + 1
                    print(count)
                    t.sleep(1)
            except Exception as e:
                print("Error {}".format(e))

    def insert(self, event):
        return self.service.events().insert(calendarId=self.settings["calendar_id"], body=event).execute()

    def update(self, event):
        return self.service.events().update(calendarId=self.settings["calendar_id"], eventId=event['id'], body=event).execute()

    def patch(self, event):
        return self.service.events().patch(calendarId=self.settings["calendar_id"], eventId=event['id'], body=event).execute()
