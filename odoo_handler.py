import erppeek

from tracker_utils import *

class OdooHandler():
    def __init__(self, settings):
        self.settings = settings
        self.worklog_columns = [{"header": "Project", "field": "issue", "style": "cyan", "no_wrap": True},
                                {"header": "Date", "field": "started", "style": "green"},
                                {"header": "Comment", "field": "comment", "style": "magenta"},
                                {"header": "Time Spent", "field": "timeSpentHumanReadable", "justify": "right", "style": "green"}]

    def update(self, events):
        self.odoo_client = erppeek.Client(
            self.settings["url"], db=self.settings["db"], user=self.settings["username"], password=self.settings["password"])
        self.model = self.odoo_client.model('hr.analytic.timesheet')

        worklogs = []
        for event in events:
            try:
                start_datetime, end_datetime = get_start_end(event)
                span_hours = (end_datetime - start_datetime).total_seconds() / 60.0 / 60.0
                if not "description" in event.keys():
                    event["description"] = ""
                comment = "{}-{} {} --- {}".format(start_datetime.time().strftime("%H:%M"),
                                                   end_datetime.time().strftime("%H:%M"), 
                                                   event["summary"], event["description"])
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
                for worklog in worklogs:
                    data = {
                        "account_id": self.settings["map"][worklog["issue"]],
                        "journal_id": self.settings["journal_id"],
                        "unit_amount": worklog["timeSpent"],
                        "date": worklog["started"],
                        "sheet_id": self.settings["time_sheet_id"],
                        "name": worklog["comment"]
                    }
                    self.model.create(data)
        else:
            print("No work has been logged for the requested day")    
