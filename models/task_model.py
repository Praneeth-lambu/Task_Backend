class TaskModel:
    def __init__(self, title, description, status, assigned_to, due_date,priority, comments):
        self.title = title
        self.description = description
        self.status = status
        self.assigned_to = assigned_to
        self.due_date = due_date
        self.priority = priority
        self.comments = comments
