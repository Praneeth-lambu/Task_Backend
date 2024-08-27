import datetime
import re

#*********Users Validations***********
def validate_name(name):
    """Validate user name."""
    return len(name) >= 4

def validate_password(password):
    """Validate user password."""
    if password is None:
        return True  # Assuming None is allowed; adjust as needed
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def validate_email(email):
    """Validate user email."""
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'
    return re.match(pattern, email) is not None

#*********Tasks Validations***********
def validate_title(title):
    """Validate task title."""
    return len(title.strip()) > 0

def validate_description(description):
    """Validate task description."""
    return len(description.strip()) > 0

def validate_status(status):
    """Validate task status."""
    valid_statuses = ["pending", "in_progress", "done"]
    return status in valid_statuses

def validate_assigned_to(assigned_to):
    """Validate task assigned user."""
    # Check if assigned_to is a valid user ID or username
    return len(assigned_to.strip()) > 0

def validate_due_date(due_date):
    """Validate task due date."""
    try:
        datetime.datetime.strptime(due_date, '%Y-%m-%d')  # Date format YYYY-MM-DD
        return True
    except ValueError:
        return False

def validate_priority(priority):
    """Validate task priority."""
    valid_priorities = {"Low", "Medium", "High"}
    return priority in valid_priorities
