from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from flask_cors import CORS
from routes.tasks import tasks_bp
from routes.users import users_bp
from routes.auth import auth_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')

# Set the secret key for JWT
    app.config['SECRET_KEY'] = 'A7C8489D681D2238728D6A8F9FD48'  # Replace with your actual secret key

    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    app.config['MONGO_CLIENT'] = client
    app.config['MONGO_DB'] = client.flask_db


    # CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": "*"}})

    CORS(app)
    
    return app
