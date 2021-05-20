import json
from timingService import TimingService
from jiraService import JiraService
from dotenv import dotenv_values

def lambda_handler(event, context):
    config = dotenv_values(".env")

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

# Main entry point if not running in AWS lambda
def main():
    print(lambda_handler({},{}))

if __name__=="__main__":
    main()
