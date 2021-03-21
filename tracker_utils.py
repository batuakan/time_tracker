import copy
import calendar
import pytz
import dateutil.parser
from datetime import datetime, date, timedelta

from rich.console import Console
from rich.table import Table
from rich import print

console = Console()

def td_format(td_object):
    seconds = int(td_object.total_seconds())
    if seconds < 60:
        seconds = 60
    periods = [
        ('y', 60*60*24*365),
        ('m', 60*60*24*30),
        ('d', 60*60*24),
        ('h', 60*60),
        ('m', 60)
    ]
    strings=[]
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            #Round the remaining seconds to a full minute
            if period_name == 'm' and seconds > 0:
                period_value = period_value + 1
            strings.append("%s%s" % (period_value, period_name))

    return " ".join(strings)

def calculate_time_span(*params):
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    begin_date = end_date  = date.today()
    if params and len(params) > 0:
        if params[0] == "today":
            pass
        elif params[0] == "yesterday":
            begin_date = end_date = (begin_date + timedelta(days=-1))
        elif params[0] in months:
            (i, j) = calendar.monthrange(begin_date.year, months.index(params[0]) + 1)
            # print(i, j)
            begin_date = date(year=begin_date.year, month=months.index(params[0]) + 1, day=1)
            end_date = date(year=begin_date.year, month=months.index(params[0]) + 1, day=j)
        elif "week" in params[0]:
            w = params[0][4:]
            d = "{}-W{}-1".format(begin_date.year, w)
            begin_date = datetime.strptime(d, "%Y-W%W-%w")
            print(begin_date)
            end_date = (begin_date + timedelta(days=7) +
                        timedelta(minutes=-1))
            print(end_date)
        elif "all" in params[0]:
            begin_date = begin_date - timedelta(days=365 * 100)
            end_date = begin_date + timedelta(days=365 * 100)
            
        else:
            begin_date = end_date = datetime.strptime(params[0], '%Y%m%d')
    timeMin = datetime.combine(begin_date, datetime.min.time())
    timeMax = datetime.combine(end_date, datetime.max.time())
    return timeMin, timeMax

def get_start_end(event):
    start_datetime = end_datetime = None
    if "start" in event and "dateTime" in event["start"]:
        start_datetime = dateutil.parser.isoparse(event["start"]["dateTime"])
    if "end" in event and "dateTime" in event["end"]:
        end_datetime = dateutil.parser.isoparse(event["end"]["dateTime"])
    return start_datetime, end_datetime

def get_value(keys, value, default = ""):
    # print(keys, value)
    keys_list = keys.split(".")
    v = value

    for key in keys_list:
        if key not in v:
            return default
        if key == keys_list[-1]:
            return v[key] 
        v = v[key]

def pretty_print(data, *columns, **kwargs):
    table = Table(title="Tasks")
    fields = []
    columns_deepcopy = copy.deepcopy(columns)
    for c in columns_deepcopy:
        fields.append(c.pop("field", None))
        table.add_column(**c)
    if type(data) is dict:
        for key, value in data.items():
            row = []
            for field in fields:
                if field == "key":
                    row.append(str(key))
                else:
                    row.append(str(get_value(field, value)))
            table.add_row(*row)
    if type(data) is list:
        for d in data:            
            row = []
            for field in fields:
                row.append(str(get_value(field, d)))
            table.add_row(*row)
    console.print(table, justify="left")

def start(event):
    s, _ = get_start_end(event)
    return s


def group_by_date(events):
    group = {}
    for event in events:
        s, _ = get_start_end(event)
        if s is None:
            continue
        s = s.date()
        if s not in group:
            group[s] = []
        group[s].append(event)
    return group

def ceil_dt(dt, delta):
    dt_min = datetime.min
    dt_min = dt_min.replace(tzinfo=pytz.UTC)
    diff = (dt_min - dt) % delta
    return dt + diff, diff.total_seconds() * -1


def floor_dt(dt, delta):
    dt_min = datetime.min
    dt_min = dt_min.replace(tzinfo=pytz.UTC)
    diff = (dt - dt_min) % delta
    return dt - diff, diff.total_seconds()

def round_dt(dt, delta):
    ceil, c_diff = ceil_dt(dt, delta)
    floor, f_diff = floor_dt(dt, delta)
    if abs(c_diff) < abs(f_diff):
        return ceil, c_diff
    return floor, f_diff
    

def elastic(events, **kwargs):
    s = None
    columns =  [{"header": "Start", "field": "start.dateTime", "style": "cyan", "no_wrap": True},
                {"header": "End", "field": "end.dateTime", "style": "magenta", "no_wrap": True},
                {"header": "Summary", "field": "summary", "style": "green"}]

    group = group_by_date(events)
    for k, v in group.items():
        group[k] = sorted(v, key=start)
       
    for k, v in group.items():
        # pretty_print(v, *columns)
        for e in v:
            s, _ = get_start_end(e)
            print(str(s))
            new_s, diff = round_dt(s, timedelta(minutes=15))
            print(str(new_s), diff)
            e["start"]["dateTime"] = new_s.isoformat()
        pretty_print(v, *columns)
