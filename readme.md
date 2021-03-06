Timing app to Jira sync
=======================

Gets all tasks from timingapp that are not prefixed with `RECORDED` and that have `[JIRA-123]` style Jira task
references in the title, notes or project name (in that order of priority). These are pushed as worklogs
to Jira and then the titles in timingapp are changed to ensure that they are not logged multiple times.

Installation
------------

This relies on Python 3 at least version 3.8

The following python packages are required:

* jira
* python-dotenv
* requests
* dateutil

These can be installed locally or globally, or as a virtual environment

e.g. globally via `pip install requests python-dotenv jira python-dateutil`

Using with Timing
-----------------

* Create tasks with `[Jira-##]` codes in the title. Add `[COMMENT]` if you want a comment added as well
* After timing app has synced (takes a couple of minutes), run script
* The sync will create time logs for all tasks that are not already marked with `RECORDED` at the start. Any with `[COMMENT]` will also be commented. Note that the text used in both timelog and comment will default to the note (if there is one), or the title if the note is blank. The jira code and `[COMMENT]` markup will be removed.
* Once a timelog is made, the timing app task will be updated with `RECORDED` - in the title, so that it is not synced again
* After a minute or two this will sync back to the timing app

Running
-------

timingapp and jira API details can be set as envionrment variables or explicitly in `.env`. An example is included in `.env.example`

Run with python3.x (eg. 3.10) as:

`python3.x ./lambda_function.py`
