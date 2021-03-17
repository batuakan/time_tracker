import copy
import calendar
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
    for d in data:            
        row = []
        for f in fields:
            row.append(str(get_value(f, d)))
        table.add_row(*row)
    console.print(table, justify="left")
