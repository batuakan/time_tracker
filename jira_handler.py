import json
import copy
import re
import dateutil.parser
from datetime import datetime, date, timedelta, timezone



from jira import JIRA
from tracker_utils import *

from jinja2 import Template

class JiraHandler():
    def __init__(self, settings):
        self.settings = settings
        # print(settings)
        options = {"server": self.settings["server"]}
        self.jira = JIRA(options=options, basic_auth=(self.settings["username"], self.settings["api_key"]))
        self.worklog_columns = [{"header": "Issue", "field":"issue", "style": "cyan", "no_wrap": True},
                                {"header": "Started", "field": "started", "style": "green"},
                                {"header": "Comment", "field": "comment", "style": "magenta"},
                                {"header": "Time Spent", "field": "timeSpent", "justify": "right", "style": "green"}]
                                
        s = json.dumps(self.settings["export_template"])
        self.export_template = Template(s)

    def update(self, events):
        worklogs = []
        for event in events:
            try:
                start_datetime, end_datetime = get_start_end(event)
                worklog = {
                    "issue": event["extendedProperties"]["private"]["jira"],
                    "timeSpent": td_format(end_datetime - start_datetime),
                    "started": start_datetime
                }
                if "description" in event.keys() and event["description"] != None:
                    worklog["comment"] = event["description"]
                else:
                    worklog["comment"] = event["summary"]
                worklogs.append(worklog)
            except:
                pass

        if worklogs != []:
            pretty_print(worklogs, *self.worklog_columns)
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":
                for worklog in worklogs:
                   self.jira.add_worklog(worklog["issue"], comment=worklog["comment"], timeSpent=worklog["timeSpent"], started=worklog["started"])
                print("The work items have been synched with Jira")
        else:
            print("No work has been logged for the requested day")

    def delete(self, *args):
        worklogs = []
        worklogs_raw = []

        (timeMin, timeMax) = calculate_time_span(*args)

        size = 100
        initial = 0
        while True:
            start = initial*size
            issues = self.jira.search_issues(self.settings['delete_jql'], start, size)
            if len(issues) == 0:
                break
            initial += 1
            key = 1
            for issue in issues:
                for worklog in self.jira.worklogs(issue):
                    worklog_started = dateutil.parser.isoparse(worklog.raw["started"])
                    if timeMin.replace(tzinfo=timezone.utc) < worklog_started.replace(tzinfo=timezone.utc) < timeMax.replace(tzinfo=timezone.utc) and worklog.raw['author']['emailAddress'] == self.settings['username']:
                        worklogs.append(worklog)
                        d = worklog.raw
                        d['issue'] = issue.raw['key']
                        worklogs_raw.append(d)
        if worklogs_raw != []:
            pretty_print(worklogs_raw, *self.worklog_columns)
            console.print("JIRA worklogs listed above will be deleted. This action cannot be undone")
            s = console.input(">[bold green]yes>[bold red]no>")
            if s == "yes":
                for worklog in worklogs:
                    worklog.delete()
                print("The work items have been deleted")


    def export_issues(self):
        issues_dict = {}
        for issue in self.find_issues(self.settings['export_jql']):
            issues_dict[issue.key] = {"summary": issue.fields.summary,
                    "description": issue.fields.description,
                    "extendedProperties": {
                    "private": {
                        "jira": issue.key,
                        "project": self.project_from_issue(issue.key)
                    }
                }
            }
        with open('jira_export.json', 'w') as f:
            json.dump(issues_dict, f, sort_keys=True, indent=4)

    def find_issues(self, jql = ""):
        size = 100
        initial = 0
        issues_dict = {}
        while True:
            start = initial*size
            issues = self.jira.search_issues(jql, start, size)
            if len(issues) == 0:
                break
            initial += 1
            key = 1
            for issue in issues:
                yield issue
                
    def project_from_issue(self, issue):
        best_match = ""
        best_score = 0
        for k,v in self.settings['odoo_map'].items():
            
            ma = re.search(str(k), issue)
            if ma:
                min, max = ma.span()
                if max - min > best_score:
                    best_score = max - min
                    best_match = v
        return best_match

    def event_from_issue(self, issue_str):

        event = None
        for issue in self.find_issues('issueKey = {}'.format(issue_str)):
            event = {"summary": issue.fields.summary,
             "description": issue.fields.description,
             "extendedProperties": {
                 "private": {
                     "jira": issue.key,
                     "project": self.project_from_issue(issue.key)
                 }
             }
             }
            if get_value("extendedProperties.private.project", event) == "":
                event['extendedProperties']['private'].pop('project', None)
        return event
