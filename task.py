class Task(dict):
    def __init__(self, jira_code, timing_code, title, start, duration, comment):
        dict.__init__(self, jira_code=jira_code, timing_code=timing_code, title=title, start=start, duration=duration, comment=comment)
