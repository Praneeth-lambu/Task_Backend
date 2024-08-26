from bson import ObjectId
from flask import Blueprint, jsonify, request, current_app
from routes.users import get_user_management
from utils.jwt_manager import token_required
from utils.validate.helpers import validate_task_data

tasks_bp = Blueprint('tasks', __name__)

def get_task_management():
    return current_app.config['MONGO_DB'].Task_management

def error_response(message, status_code):
    return jsonify({'error': message}), status_code 

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
        tasks_cursor = Task_management.find()
    else:
        tasks_cursor = Task_management.find({"assigned_to": {"$regex": f"^{user_name}$", "$options": "i"}})

    tasks = []
    for task in tasks_cursor:
        tasks.append({
            "_id": str(task["_id"]),
            "title": task.get("title"),
            "description": task.get("description"),
            "status": task.get("status"),
            "assigned_to": task.get("assigned_to"),
            "due_date": task.get("due_date")
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

        # Construct query based on user role
        if user_role == 'admin':
            query = {"title": {"$regex": title, "$options": "i"}}
        else:
            query = {
                "title": {"$regex": title, "$options": "i"},
                "assigned_to": {"$regex": f"^{user_name}$", "$options": "i"}
            }

        # Fetch tasks based on the query
        tasks = Task_management.find(query)
        tasks_list = []
        for task in tasks:
            tasks_list.append({
                "_id": str(task["_id"]),
                "title": task.get("title"),
                "description": task.get("description"),
                "status": task.get("status"),
                "assigned_to": task.get("assigned_to"),
                "due_date": task.get("due_date")
            })

        if tasks_list:
            return jsonify(tasks_list), 200
        else:
            return jsonify({'msg': "No tasks found with the specified title."}), 404

    except Exception as e:
        return jsonify({'msg': f"An error occurred: {str(e)}"}), 500
@tasks_bp.route("/addTask", methods=["POST"])
@token_required
def add_task(user_id):
    Task_management = get_task_management()
    data = request.get_json()
    required_fields = ["title", "description", "status", "assigned_to", "due_date"]

    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    title = data["title"]
    description = data["description"]
    status = data["status"]
    assigned_to = data["assigned_to"]
    due_date = data["due_date"]

    error_message, status_code = validate_task_data(title, description, status, assigned_to, due_date)
    if error_message:
        return jsonify({'msg': error_message}), status_code

    Task_management.insert_one({
        "title": title,
        "description": description,
        "status": status,
        "assigned_to": assigned_to,
        "due_date": due_date
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
    required_fields = ["title", "description", "status", "assigned_to", "due_date"]

    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    title = data["title"]
    description = data["description"]
    status = data["status"]
    assigned_to_name = data["assigned_to"]  # This is a name
    due_date = data["due_date"]

    error_message, status_code = validate_task_data(title, description, status, assigned_to_name, due_date)
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
            "due_date": due_date
        }}
    )

    if result.matched_count > 0:
        return jsonify({'msg': "Task Details Updated Successfully"}), 200
    else:
        return jsonify({'msg': "Task does not exist"}), 404
