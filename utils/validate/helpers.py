from bson import ObjectId
from flask import current_app
from utils.hashing import hash_password
from utils.validate.validations import *

def validate_task_data(title, description, status, assigned_to, due_date, priority):
   
    # Validate title
    if not validate_title(title):
        return 'Title cannot be empty', 400
    
    # Validate description
    if not validate_description(description):
        return 'Description cannot be empty', 400
    
    # Validate status
    if not validate_status(status):
        return 'Invalid status value. Must be one of: Not Started, In Progress, Completed.', 400
    
    # Validate assigned_to
    if not validate_assigned_to(assigned_to):
        return 'Invalid assigned user', 400
    
    # Validate due_date
    if not validate_due_date(due_date):
        return 'Invalid due date format. Must be in ISO format (e.g., 2024-12-31).', 400
    
    # Validate priority
    valid_priorities = {"Low", "Medium", "High"}
    if isinstance(priority, int):
        priority = {1: "Low", 2: "Medium", 3: "High"}.get(priority, None)
    
    if priority not in valid_priorities:
        return 'Invalid priority value. Must be one of: Low, Medium, High.', 400
    
    # If all validations pass
    return None, None


def validate_user_data(name, email, password):
    if not validate_name(name):
        return 'Name must be at least 4 characters long', 400
    if not validate_email(email):
        return 'Invalid email format', 400
    if not validate_password(password):
        return 'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, and one number', 400
    return None, None

def email_exists(email, exclude_id=None):
    User_management = current_app.config['MONGO_DB'].User_management
    query = {"email": email}
    if exclude_id:
        query["_id"] = {"$ne": exclude_id}
    return User_management.find_one(query)

def get_user_id(id):
    try:
        return ObjectId(id)
    except Exception:
        return None
