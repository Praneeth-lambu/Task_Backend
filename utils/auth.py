import bcrypt
import jwt
import datetime
from flask import current_app

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password_hash(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def generate_jwt(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
