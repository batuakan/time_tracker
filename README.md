Setup
=====

Copy the latest version

```console
git clone https://github.com/batuakan/time_tracker.git
```

Create a virtual environmnt to ensure smooth operation and activate it.

```console
python3 -m venv venv
```

The following packages are required to run time_tracker, please install them using pip.

```console
pip install -r requirements.txt
```

Configuration
=============

A sample settings.json file and a sample tasks.json file is provided. Copy settings.sample.json to settings.json and copy tasks.sample.json to tasks.json.

Google Calendar
---------------

1. Follow the instruction using the link below to allow access to google calendar API, download and copy the creditentials.json file into the main directory of the project. 

https://developers.google.com/calendar/quickstart/python

2. Go to https://calendar.google.com/ and click settings
3. Select the calendar you wnt to expose to time tracker and copy the calendar_id and paste into settings.json file

```json
{
    "calendar": "xxyyzz11223344@group.calendar.google.com",
}
```

JIRA Access
-----------

1. Login to jira using your companies account link. Usually company_name.atlassian.net.
2. Go to Account settings / Security / create and manage API tokens
3. Click create API token and give your API token a name e.g. time_tracker. No need to say keep your API token secret
4. Fill in your Jira settings in the settings.json file
    
```json
{
    "jira": {
        "server": "https://company_name.atlassian.net",
        "username": "yourname@company_name.com",
        "api_key": "Your API key",
        "project": "name of the project you want to export jira tasks from"
    },
}
```

Setting Up Tasks
----------------

Insert as many tasks as you want in to the tasks.json file

```json
{
    "tasks": {
        "t1": {
            "summary": "Some boring task ",
            "description": "Some very boring task that needs time reporting",
            "extendedProperties": {
                "private": {
                    "jira": "JIRA_Issue-XXX",
                    "project": "odoo_project_id"                    
                }
            }
        },
        "t2": {
            "summary": "Some other boring task ",
            "description": "Some very boring task that needs time reporting",
            "extendedProperties": {
                "private": {
                    "jira": "JIRA_Issue-XXX",
                    "project": "odoo_project_id"                    
                }
            }
        },
        "lunch": {
            "summary": "Lunch",
            "location": "Lunch place",
            "description": "Nothing like a healthy meal to rejuvenate your body and soul :)",
            "extendedProperties": {
                "private": {}
        }
    }


    }
}
```
