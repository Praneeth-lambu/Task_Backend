from flask import Blueprint, jsonify, request, current_app
from utils.hashing import hash_password, verify_password
from utils.validate.helpers import email_exists, validate_user_data
from utils.jwt_manager import encode_auth_token, decode_auth_token, token_required

auth_bp = Blueprint('auth', __name__)

def get_user_management():
    return current_app.config['MONGO_DB'].User_management

#home


# Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    usermail = data.get("email")
    password = data.get("password")
    
    User_management = get_user_management()
    user = User_management.find_one({"email": usermail})

    if user and verify_password(password, user['password']):
        token = encode_auth_token(str(user['_id']))
        if token:
            user_data = {
                "id": str(user['_id']),
                "email": user['email'],
                "name": user.get('name'),
                "role": user.get('role')  # Send role data
                # Add other user fields as needed
            }
            resp = jsonify({'token': token, 'user': user_data, 'msg': 'Successfully logged in'})
            resp.set_cookie('authToken', token, httponly=True, secure=True, samesite='Strict')  # Set HTTP-only cookie
            return resp, 200
        else:
            return jsonify({'msg': 'Failed to generate token'}), 500
    else:
        return jsonify({'msg': 'Invalid email or password'}), 401

# Register
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required_fields = ["name", "email", "password"]

    if not all(field in data for field in required_fields):
        return jsonify({'msg': "Missing fields in request"}), 400

    name = data["name"]
    email = data["email"]
    password = data["password"]

    # Validate user data
    error_msg, status_code = validate_user_data(name, email, password)
    if error_msg:
        return jsonify({'msg': error_msg}), status_code

    if email_exists(email):
        return jsonify({'msg': 'Email already exists'}), 409

    hashed_password = hash_password(password)

    User_management = get_user_management()
    User_management.insert_one({
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": "user"  # Default role for new users
    })
    return jsonify({'msg': "User Registered Successfully"}), 201

# Logout
@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout(user_id):
    # Invalidate the token on the client side (remove it from cookies or local storage)
    resp = jsonify({'msg': 'Successfully logged out'})
    resp.set_cookie('authToken', '', expires=0, httponly=True, secure=True, samesite='Strict')  # Remove auth token cookie
    return resp, 200
