Timing app to Jira sync
=======================

Gets all tasks from timingapp that are not prefixed with RECORDED and that have [JIRA-123] style Jira task
references in the title, notes or project name (in that order of priority). These are pushed as worklogs
to Jira and then the titles in timingapp are changed to ensure that they are not logged multiple times.

Installation
------------

The following python packages are required:

* jira
* python-dotenv
* requests

Running
-------

Run with python as:

python3.8 ./lambda_function.py

This requires timingapp and jira API details to be set in .env. And example is included in .env.example

