import os
from flask import Flask
from flask_mail import Mail
from pymongo import MongoClient
from flask_cors import CORS
from routes.tasks import tasks_bp
from routes.users import users_bp
from routes.auth import auth_bp
from routes.mail import mail_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(mail_bp, url_prefix='/mail')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Set the secret key for JWT
    app.config['SECRET_KEY'] = 'A7C8489D681D2238728D6A8F9FD48'  # Replace with your actual secret key

    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    app.config['MONGO_CLIENT'] = client
    app.config['MONGO_DB'] = client.flask_db

    # Flask-Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = ''  # Use environment variable names
    app.config['MAIL_PASSWORD'] = ''  # Use environment variable names
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    # Initialize CORS
    CORS(app)

    # Initialize Flask-Mail
    mail = Mail(app)

    @app.route('/')
    def home():
        return 'Welcome to the Flask application!'

    @app.route('/test')
    def test():
        return 'test route in run files'

    return app
