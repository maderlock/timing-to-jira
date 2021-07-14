#import json
from typing import Dict, List
import requests
import re
from collections.abc import Iterable
from task import Task
import json
import datetime
from dateutil import parser

class TimingService:
    project_to_jira_mapping: Dict = None
    re_jira_code = "\[([A-Z]+-\d+)\]\s?" # Used for search, extraction of code, and removal of codes
    recorded_prefix = "RECORDED"
    base_url = url = "https://web.timingapp.com/api/v1"
    ignore_window_in_secs = 300 # Set this to be the window in which, if any changes have been made, skip all updates

    def __init__(self, authkey: str) -> None:
        self._authkey = authkey

    # Get all timing tasks that have Jira information and are not reported
    # Returns empty list if any edits within cut-off window
    def get_outstanding_jira_tasks(self) -> List[Task]:
        tasks = self._convert_tasks_to_worklogs(
            self.filter_unreported(
                self.filter_jira_tasks(
                    self.get_all_timing_tasks()
                )
            )
        )
        # If edits within cutoff window, return empty list
        if (self.edits_exist_in_window(tasks)):
            return []
        return tasks

    # Gets all tasks from timing app
    def get_all_timing_tasks(self) -> Iterable: 
        path = "/time-entries"
        res = self._timing_get(path)
        return self._extract_data_from_response(res.json()) # Throws exception if does not decode sucessfully

    # Get all projects from timing app
    def get_projects_from_timing(self, hide_archived:bool=True) -> Iterable:
        path = "/projects" + ("?hide_archived=true" if hide_archived else "")
        res = self._timing_get(path)
        return self._extract_data_from_response(res.json()) # Throws exception if does not decode sucessfully

    def _get_headers(self) -> List:
        return {
            "Authorization": "Bearer " + self._authkey,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    # Make GET request of timing app
    def _timing_get(self, path:str) -> requests.Response:
        url = self.base_url + path
        headers = self._get_headers()
        res = requests.get(url, headers=headers)
        if (res.status_code != 200):
            raise ConnectionError("Non-200 response from timingapp" + res.text)
        return res

    # Make POST request of timing app
    def _timing_post(self, path:str, body:str) -> requests.Response:
        url = self.base_url + path
        headers = self._get_headers()
        res = requests.post(url, body, headers=headers)
        if (res.status_code != 200):
            raise ConnectionError("Non-200 response from timingapp" + res.text)
        return res
    
    # Make PUT request of timing app
    def _timing_put(self, path:str, json_in:json) -> requests.Response:
        url = self.base_url + path
        headers = self._get_headers()
        res = requests.put(url, None, json=json_in, headers=headers)
        if (res.status_code != 200):
            raise ConnectionError("Non-200 response from timingapp" + res.text)
        return res

    # Lazily populate project to jira mapping
    def get_projects_to_jira_mapping(self) -> Dict:
        if self.project_to_jira_mapping is None:
            self.project_to_jira_mapping = {}
            projects = self.get_projects_from_timing()
            for project in projects:
                project_code = project["self"]
                result = re.search(self.re_jira_code,project["title"])
                if result:
                    self.project_to_jira_mapping[project_code] = result.group(1)
        return self.project_to_jira_mapping

    # Extract only the tasks from the timing response
    def _extract_data_from_response(self, input:Iterable) -> Iterable:
        return input["data"]
    
    # Filter only tasks that are not already marked as imported
    def filter_unreported(self, input:Iterable) -> Iterable:
        filtered_inputs = []
        for task in input:
            if task["title"] is None or not task["title"].startswith(self.recorded_prefix):
                filtered_inputs.append(task)
        return filtered_inputs

    # Extract only tasks with Jira tasks in title or notes or in project
    # Tasks have the Jira codes removed and added against a specific jira_code key
    def filter_jira_tasks(self, input:Iterable) -> Iterable:
        filtered_inputs = []
        for task in input:
            task["original_title"] = task["title"]
            # Try to find jira code in title first
            if (not task["title"] is None):
                result = re.search(self.re_jira_code, task["title"])
                if result:
                    task["jira_code"] = result.group(1)
                    task["title"] = re.sub(rf"{self.re_jira_code}", "", task["title"])
                    filtered_inputs.append(task)
                    continue
            # Try to find jira code in notes next
            if (not task["notes"] is None):
                result = re.search(self.re_jira_code, task["notes"])
                if result:
                    task["jira_code"] = result.group(1)
                    task["notes"] = re.sub(rf"{self.re_jira_code}", "", task["notes"])
                    filtered_inputs.append(task)
                    continue
            # Fall-back - look at project and see if it has a Jira code mapping in it
            if (
                not task["project"] is None and
                not task["project"]["self"] is None and
                task["project"]["self"] in self.get_projects_to_jira_mapping()
            ):
                task["jira_code"] = self.get_projects_to_jira_mapping()[task["project"]["self"]]
                filtered_inputs.append(task)
                continue
        return filtered_inputs

    # Were any tasks changed in the last 5 minutes
    def edits_exist_in_window(self, input:Iterable) -> bool:
        # As modification time is not available in API, have to ignore and just return False
        return False
        # now = datetime.now()
        # for task in input:
        #     start_time = parser.parse(task["start_date"]) #todo: handle exceptions, and use mofified time... oh, that does not exist :(
        #     seconds_ago = (now-start_time).total_seconds()
        #     if(seconds_ago < self.ignore_window_in_secs):
        #         return True
        # return False

    # Extract the Jira task, duration, datetime start and comment for each task
    def _convert_tasks_to_worklogs(self, input:Iterable) -> List[Task]:
        output_tasks = [];
        for task in input:
            output_tasks.append(self._convert_task_to_worklog(task))
        return output_tasks
    
    # Convert data from timing app to task object for pushing to Jira
    #
    # TODO: Use information from projects. Also need this when filtering
    # Logic: TODO
    def _convert_task_to_worklog(self, task_input) -> Task:
        return Task(
            task_input["jira_code"],
            task_input["self"],
            task_input["original_title"],
            task_input["start_date"],
            task_input["duration"],
            task_input["notes"] if not (task_input["notes"] is None or task_input["notes"] == "") else task_input["title"]
        )

    # Change timing tasks so that they are marked as recorded
    def record_tasks(self, tasks:List[Task]) -> None:
        for task in tasks:
            self._record_task(task)

    # Mark a timing task as recorded so that it is not picked up again in the future
    def _record_task(self, task:Task) -> None:
        path = task["timing_code"] # This includes the prefix of /time-entries/ and the ID
        body = {
            "title": self.recorded_prefix + " - " + task["title"]
        }
        res = self._timing_put(path, body)
        # TODO: Confirm if worked by whether title contains RECORDED