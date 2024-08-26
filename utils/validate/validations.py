
import datetime
import re

        #*********Users Validations***********
# """Validate user name."""
def validate_name(name):
    return len(name) >= 4

# """Validate user password."""
def validate_password(password):
    if password is None:
        return True
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
    import re
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'
    return re.match(pattern, email) is not None


        #*********Tasks Validations***********
def validate_title(title):
    return len(title) > 0

def validate_description(description):
    return len(description) > 0

def validate_status(status):
    valid_statuses = ["pending", "in_progress", "done"]
    return status in valid_statuses

def validate_assigned_to(assigned_to):
    # Check if assigned_to is a valid user ID or username
    return len(assigned_to) > 0

def validate_due_date(due_date):

    try:
        datetime.datetime.strptime(due_date, '%Y-%m-%d')  # Example date format YYYY-MM-DD
        return True
    except ValueError:
        return False
