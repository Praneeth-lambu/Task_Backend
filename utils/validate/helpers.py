from bson import ObjectId
from flask import current_app
from utils.hashing import hash_password
from utils.validate.validations import *

def validate_task_data(title, description, status, assigned_to, due_date):
    if not validate_title(title):
        return 'Title cannot be empty', 400
    if not validate_description(description):
        return 'Description cannot be empty', 400
    if not validate_status(status):
        return 'Invalid status value', 400
    if not validate_assigned_to(assigned_to):
        return 'Invalid assigned user', 400
    if not validate_due_date(due_date):
        return 'Invalid due date format', 400
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
