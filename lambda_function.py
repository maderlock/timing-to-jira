import json

import sys
import os
from timingService import TimingService
from jiraService import JiraService
from dotenv import dotenv_values

def lambda_handler(event, context):

    # Load configuration from .env or environment variables
    envir = {
        **dotenv_values(".env"),
        **os.environ
    }

    # Pull out needed config
    try:
        if ("user" in event):
            name = event["user"].upper()
            config = get_config_from_env(envir, name);
        else:
            config = get_config_from_env(envir, None);
    except AssertionError as err:
        return {
            'statusCode': 400,
            'body': "Error getting config: " + str(err.args)
        }

    # Get outstanding tasks to push to Jira
    timingService = TimingService(config["TIMING_API_KEY"])
    try:
        tasks = timingService.get_outstanding_jira_tasks()
    except Exception as exc:
        return {
            'statusCode': 500,
            'body': "Error getting tasks: " + str(exc)
        }
    # Push timelog of tasks to Jira
    jiraService = JiraService(
        config["JIRA_ENDPOINT"],
        config["JIRA_LOGIN_USER"],
        config["JIRA_LOGIN_KEY"],
        config["JIRA_LOGGING_USER_ID"]
    )
    try:
        logged_tasks = jiraService.push_timelogs_from_tasks(tasks)
    except Exception as exc:
        return {
            'statusCode': 500,
            'body': "Error recording tasks in Jira: " + str(exc)
        }
    # Update timing app so these do not get pulled in again
    try:
        timingService.record_tasks(logged_tasks)
    except Exception as exc:
        return {
            'statusCode': 500,
            'body': "Error updating tasks in timingpp: " + str(exc)
        }
    # Send success response
    return {
        'statusCode': 200,
        'body': json.dumps(logged_tasks)
    }

# Extract config options from environment variables, optionally based on user name
def get_config_from_env(envir, name):
    # Configuration keys that we need to be defined
    _conf_keys = [
        "JIRA_ENDPOINT",
        "JIRA_LOGIN_USER",
        "JIRA_LOGIN_KEY",
        "JIRA_LOGGING_USER_ID",
        "TIMING_API_KEY"
    ]
    retConfig = {}
    # Name-specific env variables
    if (not name is None):
        for key in _conf_keys:
            key_name = name + "_" + key
            if (not key_name in envir):
                raise AssertionError("No value set for environment variable " + key_name);
            retConfig[key] = envir[name + "_" + key]
    # Non-name specific variables
    else:
        for key in _conf_keys:
            if (not key in envir):
                raise AssertionError("No value set for environment variable " + key);
            retConfig[key] = envir[key]
    return retConfig

# Main entry point if not running in AWS lambda
def main():
    if (len(sys.argv) >= 2):
        input = {"user":sys.argv[1]}
    else:
        input = {}
    print(lambda_handler(input,{}))

if __name__=="__main__":
    main()
