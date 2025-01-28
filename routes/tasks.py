# models/tasks.py (or similar)
from datetime import datetime
from bson import ObjectId
import re
from flask import Blueprint, jsonify, request, current_app
from routes.users import get_user_management
from utils.jwt_manager import token_required
from utils.validate.helpers import validate_task_data

tasks_bp = Blueprint('tasks', __name__)

#Task managemenet collection
def get_task_management():
    return current_app.config['MONGO_DB'].Task_management

#handle Error response
def error_response(message, status_code):
    return jsonify({'error': message}), status_code

# serialize_objectid for comments 
def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_objectid(item) for item in obj]
    else:
        return obj

#get all Tasks
@tasks_bp.route("/getTask/", methods=["GET"])
@token_required
def get_tasks(user_id):
    Task_management = get_task_management()
    user_collection = get_user_management()

    user = user_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    user_role = user.get("role")
    user_name = user.get("name").lower()  # Normalize case for comparison

    if user_role == 'admin':
        tasks_cursor = Task_management.find().sort("priority", -1)  # Ascending order
    else:
        tasks_cursor = Task_management.find({"assigned_to": {"$regex": f"^{user_name}$", "$options": "i"}}).sort("priority", -1)

    tasks = []
    for task in tasks_cursor:
        tasks.append({
            "_id": str(task["_id"]),  # Convert ObjectId to string
            "title": task.get("title"),
            "description": task.get("description"),
            "status": task.get("status"),
            "assigned_to": task.get("assigned_to"),
            "due_date": task.get("due_date"),
            "priority": task.get("priority_label"),  # Use priority_label for display
            "comments": serialize_objectid(task.get("comments", []))  # Include comments
        })

    if tasks:
        return jsonify(tasks), 200
    else:
        return jsonify({'msg': "You don't have any tasks assigned to you."}), 404


#get Task by title or description
@tasks_bp.route("/getTask/<string:title>", methods=["GET"])
@token_required
def get_task(user_id, title):
    try:
        Task_management = get_task_management()
        user_collection = get_user_management()

        # Get user details
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({'msg': 'User not found'}), 404

        user_role = user.get("role")
        user_name = user.get("name").lower()  # Normalize case for comparison

        # Sanitize the title and description to handle special characters
        sanitized_title = re.escape(title)
        sanitized_description = re.escape(title)

        # Construct query based on user role and provided filters
        if user_role == 'admin':
            query = {
                "$or": [
                    {"title": {"$regex": sanitized_title, "$options": "i"}},
                    {"description": {"$regex": sanitized_description, "$options": "i"}}
                ]
            }
            if sanitized_description:
                query["description"] = {"$regex": sanitized_description, "$options": "i"}
        else:
            query = {
                "$or": [
                    {"title": {"$regex": sanitized_title, "$options": "i"}},
                    {"description": {"$regex": sanitized_description, "$options": "i"}}
                ],
                "assigned_to": {"$regex": f"^{user_name}$", "$options": "i"}
            }

        # Fetch tasks based on the query
        tasks = Task_management.find(query).sort("priority", -1)
        tasks_list = []
        for task in tasks:
            tasks_list.append({
                "_id": str(task["_id"]),  # Convert ObjectId to string
                "title": task.get("title"),
                "description": task.get("description"),
                "status": task.get("status"),
                "assigned_to": task.get("assigned_to"),
                "due_date": task.get("due_date"),
                "priority": task.get("priority_label"),  # Use priority_label for display
                "comments": serialize_objectid(task.get("comments", []))  # Include comments
            })

        if tasks_list:
            return jsonify(tasks_list), 200
        else:
            return jsonify({'msg': "No tasks found with the specified criteria."}), 404

    except Exception as e:
        return jsonify({'msg': f"An error occurred: {str(e)}"}), 500
 
#Add Task
@tasks_bp.route("/addTask", methods=["POST"])
@token_required
def add_task(user_id):
    Task_management = get_task_management()
    User_management = get_user_management()


    data = request.get_json()
    required_fields = ["title", "description", "status", "assigned_to", "due_date", "priority"]

    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    title = data["title"]
    description = data["description"]
    status = data["status"]
    assigned_to = data["assigned_to"]
    due_date = data["due_date"]
    priority = data["priority"]

    priority_mapping = {
        'Low': 1,
        'Medium': 2,
        'High': 3
    }
    
    priority_numeric = priority_mapping.get(priority, 1)  # Default to 'Low' if not found
    priority_label = priority  # Use the provided label for display

    error_message, status_code = validate_task_data(title, description, status, assigned_to, due_date, priority_numeric)
    if error_message:
        return jsonify({'msg': error_message}), status_code
    
    user_query = {"name": re.compile(f"^{re.escape(assigned_to)}$", re.IGNORECASE)}
    assigned_user = User_management.find_one(user_query)
    if not assigned_user:
        return jsonify({'msg': "Assigned user not found"}), 404

    # Add the task with an initial history entry
    Task_management.insert_one({
        "title": title,
        "description": description,
        "status": status,
        "assigned_to": assigned_to,
        "due_date": due_date,
        "priority": priority_numeric,  # Numeric value for sorting
        "priority_label": priority_label,  # String label for display
        "comments": [],  # Initialize comments as an empty list
        "history": [  # Initialize history with a creation record
            {
                "changed_by": "System",  # or "Admin" if preferred
                "change_time": datetime.utcnow(),
                "changes": {
                    "title": {
                        "old_value": None,
                        "new_value": title
                    },
                    "description": {
                        "old_value": None,
                        "new_value": description
                    },
                    "status": {
                        "old_value": None,
                        "new_value": status
                    },
                    "assigned_to": {
                        "old_value": None,
                        "new_value": assigned_to
                    },
                    "due_date": {
                        "old_value": None,
                        "new_value": due_date
                    },
                    "priority": {
                        "old_value": None,
                        "new_value": priority_label
                    }
                }
            }
        ]
    })
    return jsonify({'msg': "Task Added Successfully"}), 201

#Delete task
@tasks_bp.route("/deleteTask/<id>", methods=["DELETE"])
@token_required
def delete_task(user_id, id):
    Task_management = get_task_management()
    try:
        task_id = ObjectId(id)
    except Exception:
        return jsonify({'msg': "Invalid ID format"}), 400

    result = Task_management.delete_one({"_id": task_id})
    if result.deleted_count > 0:
        return jsonify({'msg': "Task Deleted Successfully"}), 200
    else:
        return jsonify({'msg': "No task to delete"}), 404

#Update Task
@tasks_bp.route("/updateTask/<id>", methods=["PUT"])
@token_required
def update_task(user_id, id):
    Task_management = get_task_management()
    User_management = get_user_management()
    data = request.get_json()
    required_fields = ["title", "description", "status", "assigned_to", "due_date", "priority"]

    # Check if all required fields are present
    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    title = data["title"]
    description = data["description"]
    status = data["status"]
    assigned_to_name = data["assigned_to"]
    due_date = data["due_date"]
    priority = data["priority"]

    # Priority mapping from string to numeric for sorting
    priority_mapping = {
        'Low': 1,
        'Medium': 2,
        'High': 3
    }
    
    # Convert priority to numeric and keep the label for display
    priority_numeric = priority_mapping.get(priority, 1)  # Use None if not found
    priority_label = priority  # Keep the string label for display

    # Validate data
    error_message, status_code = validate_task_data(title, description, status, assigned_to_name, due_date, priority_label)
    if error_message:
        return jsonify({'msg': error_message}), status_code

    try:
        task_id = ObjectId(id)
    except Exception:
        return jsonify({'msg': "Invalid ID format"}), 400
    user_query = {"name": re.compile(f"^{re.escape(assigned_to_name)}$", re.IGNORECASE)}
    assigned_user = User_management.find_one(user_query)
    if not assigned_user:
        return jsonify({'msg': "Assigned user not found"}), 404
    # Find the task to update
    task = Task_management.find_one({"_id": task_id})
    if not task:
        return jsonify({'msg': "Task not found"}), 404

    # Find the current user
    current_user = User_management.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        return jsonify({'msg': "User not found"}), 404

    current_user_name = current_user.get("name").lower()
    user_role = current_user.get("role")

    # Check if the user is authorized to update this task
    if user_role != 'admin' and task["assigned_to"].lower() != current_user_name:
        return jsonify({'msg': "Not authorized to update this task"}), 403

    # Collect changes
    changes = {}
    if task.get("title") != title:
        changes["title"] = {
            "old_value": task.get("title"),
            "new_value": title
        }
    if task.get("description") != description:
        changes["description"] = {
            "old_value": task.get("description"),
            "new_value": description
        }
    if task.get("status") != status:
        changes["status"] = {
            "old_value": task.get("status"),
            "new_value": status
        }
    if task.get("assigned_to") != assigned_to_name:
        changes["assigned_to"] = {
            "old_value": task.get("assigned_to"),
            "new_value": assigned_to_name
        }
    if task.get("due_date") != due_date:
        changes["due_date"] = {
            "old_value": task.get("due_date"),
            "new_value": due_date
        }
    if task.get("priority_label") != priority_label:
        changes["priority"] = {
            "old_value": task.get("priority_label"),
            "new_value": priority_label
        }

            # Create the update operations
    update_operations = {
        "$set": {
            "title": title,
            "description": description,
            "status": status,
            "assigned_to": assigned_to_name,
            "due_date": due_date,
            "priority": priority_numeric,  # Numeric priority for sorting
            "priority_label": priority_label  # String priority label for display
        }
    }

    # Conditionally add the $push operation if there are changes
    if changes:
        update_operations['$push'] = {
            'history': {
                "changed_by": current_user.get("name", "Unknown"),
                "change_time": datetime.utcnow(),
                "changes": changes
            }
        }

# Perform the update operation
    result = Task_management.update_one(
        {"_id": task_id},
        update_operations
    )

    if result.matched_count > 0:
        return jsonify({'msg': "Task Details Updated Successfully"}), 200
    else:
        return jsonify({'msg': "Task does not exist"}), 404

#Add comments
@tasks_bp.route("/addComment/<task_id>", methods=["POST"])
@token_required
def add_comment(user_id, task_id):
    Task_management = get_task_management()
    User_management = get_user_management()
    data = request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({'msg': "Comment text is required"}), 400

    try:
        task_id = ObjectId(task_id)
    except Exception:
        return jsonify({'msg': "Invalid Task ID format"}), 400

    user = User_management.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({'msg': 'User not found'}), 404

    author_name = user.get("name", "Unknown")  # Get the author's name

    Task_management.update_one(
        {"_id": task_id},
        {'$push': {
            "comments": {
                "text": text,
                "user": ObjectId(user_id),
                "author": author_name,  # Add author's name to the comment
                "createdAt": datetime.utcnow()
            }
        }}
    )

    return jsonify({'msg': "Comment Added Successfully"}), 201

#Get comments
@tasks_bp.route("/getComments/<task_id>", methods=["GET"])
@token_required
def get_comments(user_id, task_id):
    Task_management = get_task_management()

    try:
        task_id = ObjectId(task_id)
    except Exception:
        return jsonify({'msg': "Invalid Task ID format"}), 400

    task = Task_management.find_one({"_id": task_id})
    if not task:
        return jsonify({'msg': "Task not found"}), 404

    comments = task.get("comments", [])
    
    # Convert ObjectId to string for serialization
    for comment in comments:
        comment['user'] = str(comment.get('user'))  # Ensure 'user' field is a string
        comment['createdAt'] = comment.get('createdAt', datetime.utcnow()).isoformat()  # Format datetime

    return jsonify(comments), 200

@tasks_bp.route("/getTaskHistory/<string:task_id>", methods=["GET"])
@token_required
def get_task_history(user_id, task_id):
    try:
        Task_management = get_task_management()

        task = Task_management.find_one({"_id": ObjectId(task_id)}, {"history": 1})
        if not task:
            return jsonify({'msg': 'Task not found'}), 404

        return jsonify({"history": task.get("history", [])}), 200
    except Exception as e:
        return jsonify({'msg': f"An error occurred: {str(e)}"}), 500
