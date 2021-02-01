Setup
=====

The following packages are required to run time_tracker, please install them using pip.

pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install --upgrade jira
pip install --upgrade rich

Configuration
=============


Google Calendar
---------------

1.  Follow the instruction using the link below to allow access to google calendar API, download and copy the creditentials.json file into the main directory of the project. 

https://developers.google.com/calendar/quickstart/python

2. Go to https://calendar.google.com/ and click settings
3. SElect the calendar you wnt to expose to time tracker and copy the calendar_id and paste into tasks.json file

```json
{
    "calendar": "fmmeamr8vlrrd07l774bjvsq48@group.calendar.google.com",
}
```

JIRA Access
-----------

1. Login to jira using your companies account link. Usually company_name.atlassian.net.
2. Go to Account settings / Security / create and manage API tokens
3. Click create API token and give your API token a name e.g. time_tracker. No need to say keep your API token secret
4. Fill in your Jira settings in the task.json file
    
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
