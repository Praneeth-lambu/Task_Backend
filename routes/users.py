from flask import Blueprint, jsonify, request, current_app
from bson import ObjectId
from utils.hashing import hash_password
from utils.validate.helpers import email_exists, get_user_id, validate_user_data
from utils.jwt_manager import token_required
from utils.role_decorator import role_required

users_bp = Blueprint('users', __name__)

# Helper function to get User_management collection
def get_user_management():
    return current_app.config['MONGO_DB'].User_management

def error_response(message, status_code):
    return jsonify({'error': message}), status_code

# Get all users
@users_bp.route("/getUser/", methods=["GET"])
@token_required
@role_required(['admin'])
def get_all_users(user_id):
    User_management = get_user_management()
    users = []
    
    for user in User_management.find():  # Retrieve all users
        users.append({
            "_id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role")  # Default role to 'user' if not present
        })
        
    if users:
        return jsonify(users), 200
    else:
        return jsonify({'msg': "No users found"}), 404

# Get selected user by name
@users_bp.route("/getUser/<string:name>", methods=["GET"])
@token_required
@role_required(['admin'])
def get_user(user_id, name):
    User_management = get_user_management()
    try:
        # Find users by name using a case-insensitive regex search
        users_cursor = User_management.find({"name": {"$regex": name, "$options": "i"}})
        users_list = []
        for user in users_cursor:
            users_list.append({
                "_id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role", "user")  # Default role to 'user' if not present
            })
        
        if users_list:
            return jsonify(users_list), 200
        else:
            return jsonify({'msg': "No users found with the specified name."}), 404
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}", 500)

# Add a user
@users_bp.route("/addUser", methods=["POST"])
@token_required
@role_required(['admin'])
def add_user(user_id):
    data = request.get_json()
    required_fields = ["name", "email", "password"]
    optional_fields = ["role"]

    # Ensure required fields are present
    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    name = data["name"]
    email = data["email"].lower()
    password = data["password"]

    # Optional role field, default to 'user'
    role = data.get("role", "user")

    # Validate the role if provided
    if role not in ["user", "admin"]:
        return jsonify({'msg': "Invalid role. Must be 'user' or 'admin'"}), 400

    # Validate user data
    error_msg, status_code = validate_user_data(name, email, password)
    if error_msg:
        return jsonify({'msg': error_msg}), status_code

    if email_exists(email):
        return jsonify({'msg': 'Email already exists'}), 409

    # Hash the password
    hashed_password = hash_password(password)

    # Insert the new user into the database
    User_management = get_user_management()
    User_management.insert_one({
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": role  # Include the role in the new user document
    })

    return jsonify({'msg': "User Added Successfully"}), 201

# Delete a user
@users_bp.route("/deleteUser/<id>", methods=["DELETE"])
@token_required
@role_required(['admin'])
def delete_user(user_id, id):
    User_management = get_user_management()
    try:
        user_id = ObjectId(id)
    except Exception:
        return jsonify({'msg': "Invalid ID format"}), 400
    
    result = User_management.delete_one({"_id": user_id})
    if result.deleted_count > 0:
        return jsonify({'msg': "User Deleted Successfully"}), 200
    else:
        return jsonify({'msg': "No user to delete"}), 404

# Update user details
@users_bp.route("/updateUser/<id>", methods=["PUT"])
@token_required
@role_required(['admin'])
def update_user(user_id, id):
    data = request.get_json()
    required_fields = ["name", "email"]
    
    # Ensure required fields are present
    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    name = data["name"]
    email = data["email"].lower()
    password = data.get("password")  # Password is optional
    role = data.get("role")  # Role is also optional

    # Validate the role if provided
    if role and role not in ["user", "admin"]:
        return jsonify({'msg': "Invalid role. Must be 'user' or 'admin'"}), 400

    # Validate user data
    error_msg, status_code = validate_user_data(name, email, password)
    if error_msg:
        return jsonify({'msg': error_msg}), status_code

    user_id = get_user_id(id)
    if not user_id:
        return jsonify({'msg': "Invalid ID format"}), 400

    # Check if the email already exists
    if email_exists(email, exclude_id=user_id):
        return jsonify({'msg': 'Email already exists for another user'}), 409

    updates = {
        "name": name,
        "email": email,
    }

    # Only update password if provided
    if password:
        hashed_password = hash_password(password)
        updates["password"] = hashed_password

    # Only update role if provided
    if role:
        updates["role"] = role

    User_management = get_user_management()
    result = User_management.update_one(
        {"_id": user_id},
        {'$set': updates}
    )
    if result.matched_count > 0:
        return jsonify({'msg': "User Details Updated Successfully"}), 200
    else:
        return jsonify({'msg': "User Does not exist"}), 404
