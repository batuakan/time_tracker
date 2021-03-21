from datetime import datetime, date, timedelta
from tracker_utils import *

from O365 import Account, FileSystemTokenBackend


class O365Calendar():
    def __init__(self, settings):
        self.settings = settings
        credentials = (settings['client_id'],
                       settings['client_secret'])

        token_backend = FileSystemTokenBackend(
            token_path='tokens', token_filename='o365token.txt')
        account = Account(credentials, token_backend=token_backend)
        if account.is_authenticated:
            print('Authenticated!')

        self.schedule = account.schedule()
        self.calendar = self.schedule.get_calendar(calendar_name="worklog")
        self.o365event = None

    def start(self, entry):
        self.o365event = self.calendar.new_event()  # creates a new unsaved event
        self.o365event.subject = entry['summary']
        self.o365event.body = entry['description']
        self.o365event.start = datetime.now()
        self.o365event.end = datetime.now() + timedelta(minutes=30)
        self.o365event.remind_before_minutes = -1
        self.o365event.save()


    def end(self):
        if not self.o365event is None:
            self.o365event.end = datetime.now()
            self.o365event.save()
            self.o365event = None


    def fetch(self, *args):
        page_token = None
        timeMin, timeMax = calculate_time_span(*args)
        events = []
        q = self.calendar.new_query('start').greater_equal(timeMin)
        q.chain('and').on_attribute('end').less_equal(timeMax)

        # include_recurring=True will include repeated events on the result set.
        events = self.calendar.get_events(query=q, include_recurring=False)

        for event in events:
            print(event.subject)

        
