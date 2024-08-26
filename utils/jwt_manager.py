import jwt
import datetime
from functools import wraps
from flask import current_app, request, jsonify

def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        print(f"Error encoding token: {str(e)}")
        return None

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        print("Decoded payload:", payload)  # For debugging
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'msg': 'Authorization header is missing'}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != 'Bearer':
            return jsonify({'msg': 'Invalid Authorization Header'}), 401

        token = parts[1]
        try:
            # Decode the token
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload.get('sub')
            
            if not user_id:
                return jsonify({'msg': 'Invalid token payload'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'msg': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'msg': 'Invalid token'}), 401

        return f(user_id, *args, **kwargs)

    return decorated_function
