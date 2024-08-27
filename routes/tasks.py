# models/task_model.py (or similar)
from datetime import datetime
from bson import ObjectId
import re
from flask import Blueprint, jsonify, request, current_app
from routes.users import get_user_management
from utils.jwt_manager import token_required
from utils.validate.helpers import validate_task_data

tasks_bp = Blueprint('tasks', __name__)

def get_task_management():
    return current_app.config['MONGO_DB'].Task_management

def error_response(message, status_code):
    return jsonify({'error': message}), status_code

def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_objectid(item) for item in obj]
    else:
        return obj


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
        tasks_cursor = Task_management.find().sort("priority", 1)  # Sort by priority
    else:
        tasks_cursor = Task_management.find({"assigned_to": {"$regex": f"^{user_name}$", "$options": "i"}}).sort("priority", 1)

    tasks = []
    for task in tasks_cursor:
        tasks.append({
            "_id": str(task["_id"]),  # Convert ObjectId to string
            "title": task.get("title"),
            "description": task.get("description"),
            "status": task.get("status"),
            "assigned_to": task.get("assigned_to"),
            "due_date": task.get("due_date"),
            "priority": task.get("priority"),
            "comments": serialize_objectid(task.get("comments", []))  # Include comments
        })

    if tasks:
        return jsonify(tasks), 200
    else:
        return jsonify({'msg': "You don't have any tasks assigned to you."}), 404


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

        # Get description parameter from query string
        description_query = request.args.get('description', '').strip()

        # Sanitize the title and description to handle special characters
        sanitized_title = re.escape(title)
        sanitized_description = re.escape(description_query)

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
        tasks = Task_management.find(query).sort("priority", 1)
        tasks_list = []
        for task in tasks:
            tasks_list.append({
                "_id": str(task["_id"]),  # Convert ObjectId to string
                "title": task.get("title"),
                "description": task.get("description"),
                "status": task.get("status"),
                "assigned_to": task.get("assigned_to"),
                "due_date": task.get("due_date"),
                "priority": task.get("priority"),
                "comments": serialize_objectid(task.get("comments", []))  # Include comments
            })

        if tasks_list:
            return jsonify(tasks_list), 200
        else:
            return jsonify({'msg': "No tasks found with the specified criteria."}), 404

    except Exception as e:
        return jsonify({'msg': f"An error occurred: {str(e)}"}), 500
@tasks_bp.route("/addTask", methods=["POST"])
@token_required
def add_task(user_id):
    Task_management = get_task_management()
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

    error_message, status_code = validate_task_data(title, description, status, assigned_to, due_date, priority)
    if error_message:
        return jsonify({'msg': error_message}), status_code

    Task_management.insert_one({
        "title": title,
        "description": description,
        "status": status,
        "assigned_to": assigned_to,
        "due_date": due_date,
        "priority": priority,
        "comments": []  # Initialize comments as an empty list
    })
    return jsonify({'msg': "Task Added Successfully"}), 201

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

@tasks_bp.route("/updateTask/<id>", methods=["PUT"])
@token_required
def update_task(user_id, id):
    Task_management = get_task_management()
    User_management = get_user_management()
    data = request.get_json()
    required_fields = ["title", "description", "status", "assigned_to", "due_date", "priority"]

    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    title = data["title"]
    description = data["description"]
    status = data["status"]
    assigned_to_name = data["assigned_to"]  # This is a name
    due_date = data["due_date"]
    priority = data["priority"]

    error_message, status_code = validate_task_data(title, description, status, assigned_to_name, due_date, priority)
    if error_message:
        return jsonify({'msg': error_message}), status_code

    try:
        task_id = ObjectId(id)
    except Exception:
        return jsonify({'msg': "Invalid ID format"}), 400

    task = Task_management.find_one({"_id": task_id})
    if not task:
        return jsonify({'msg': "Task not found"}), 404

    current_user = User_management.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        return jsonify({'msg': "User not found"}), 404

    current_user_name = current_user.get("name").lower()
    user_role = current_user.get("role")
    
    if user_role != 'admin' and task["assigned_to"].lower() != current_user_name:
        return jsonify({'msg': "Not authorized to update this task"}), 403

    result = Task_management.update_one(
        {"_id": task_id},
        {'$set': {
            "title": title,
            "description": description,
            "status": status,
            "assigned_to": assigned_to_name,
            "due_date": due_date,
            "priority": priority
        }}
    )

    if result.matched_count > 0:
        return jsonify({'msg': "Task Details Updated Successfully"}), 200
    else:
        return jsonify({'msg': "Task does not exist"}), 404

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
