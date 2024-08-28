from functools import wraps
from flask import jsonify, current_app
from bson import ObjectId

def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(user_id, *args, **kwargs):
            User_management = current_app.config['MONGO_DB'].User_management
            user = User_management.find_one({"_id": ObjectId(user_id)})

            if not user:
                return jsonify({'msg': 'User not found'}), 404
            
            user_role = user.get("role")
            if user_role not in required_roles:
                return jsonify({'msg': "You don't have permission to access this resource"}), 403
            
            return f(user_id, *args, **kwargs)
        
        return decorated_function
    
    return decorator
