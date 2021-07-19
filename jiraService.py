
from task import Task
from typing import List
from jira import JIRA
from datetime import datetime
import json

class JiraService:
    _jira: JIRA = None

    def __init__(self, endpoint:str, email:str, api_token: str, user_id: str) -> None:
        self._endpoint = endpoint
        self._jira_email = email
        self._jira_api_token = api_token
        self._user_id = user_id

    def _jira_conn(self) -> JIRA:
        if self._jira is None:
            self._jira = JIRA(self._endpoint, basic_auth=(self._jira_email, self._jira_api_token))
        return self._jira

    def test(self) -> str:
        return 

    # Push timelogs from given Tasks
    # Returns list of those tasks that were pushed
    def push_timelogs_from_tasks(self, tasks:List[Task]) -> List:
        successes = []
        for task in tasks:
            timelogResult = self._push_timelog_from_task(task)
            # Take timelog result as the important result of whether to mark as recorded
            if (timelogResult != False):
                successes.append(task)
            if (task["as_comment"]):
                self._push_comment_from_task(task)
        return successes

    # Push task details as worklog
    def _push_timelog_from_task(self, task:Task) -> bool:
        try:
            self._jira_conn().add_worklog(
                task["jira_code"],
                None,
                round(task["duration"]), 
                None,
                None,
                None,
                task["comment"],
                datetime.fromisoformat(task["start"]),
                self._user_id
            )
            return True
        except Exception as exc:
            return False
    
    # Push task details as comment
    def _push_comment_from_task(self, task:Task) -> bool:
        try:
            self._jira_conn().add_comment(
                task["jira_code"],
                task["comment"]
            )
            return True
        except Exception as exc:
            return False
