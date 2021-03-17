import json
import csv

import dateutil.parser
from datetime import datetime, date, timedelta, timezone

from tracker_utils import *




class OdooHandler():
    def __init__(self, settings):
        self.settings = settings
        self.worklog_columns = [{"header": "Project", "field": "issue", "style": "cyan", "no_wrap": True},
                                {"header": "Date", "field": "started", "style": "green"},
                                {"header": "Comment", "field": "comment", "style": "magenta"},
                                {"header": "Time Spent", "field": "timeSpentHumanReadable", "justify": "right", "style": "green"}]

    def update(self, events):
        worklogs = []
        for event in events:
            try:
                start_datetime = dateutil.parser.isoparse(
                                    event["start"]["dateTime"])
                end_datetime = dateutil.parser.isoparse(
                                    event["end"]["dateTime"])

                print(start_datetime, end_datetime)
                span_hours = (end_datetime - start_datetime).total_seconds() / 60.0 / 60.0
                if not "description" in event.keys():
                    event["description"] = ""
                comment = "{}-{} {} --- {}".format(start_datetime.time().strftime("%H:%M"), end_datetime.time().strftime("%H:%M"), event["summary"], event["description"])
                worklogs.append({"issue": event["extendedProperties"]["private"]["project"],
                                 "timeSpent": str(span_hours),
                                 "timeSpentHumanReadable": td_format(end_datetime - start_datetime),
                                 "comment": comment,
                                 "started": start_datetime.date().strftime("%Y-%m-%d")})
            except Exception as e:
                pass
            
        if worklogs != []:
            pretty_print(worklogs, *self.worklog_columns)
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":               
                with open('odoo.csv', 'w', newline='') as csvfile:
                    odoowriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    odoowriter.writerow(["id", "timesheet_ids/name", "timesheet_ids/account_id/id", "timesheet_ids/date", "timesheet_ids/unit_amount", "timesheet_ids/journal_id/id"])
                    for worklog in worklogs:
                        odoowriter.writerow(["", worklog["comment"], self.settings["map"][worklog["issue"]], worklog["started"],  worklog["timeSpent"], "hr_timesheet.analytic_journal"]) 

                print("The work items have been written to odoo.csv file.")
        else:
            print("No work has been logged for the requested day")    
