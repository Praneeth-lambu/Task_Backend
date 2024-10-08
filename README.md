# Flask Task Management API
## Overview
This Flask-based API provides functionalities for user management and task management. It includes user authentication, user management (creation, update, deletion), and task management (creation, update, deletion). The API uses JWT tokens for authentication and MongoDB for data storage.


## Features
### User Authentication:
* Register
* login
* logout
### User Management:
* Add
* update
* delete
* retrieve users.
### Task Management:
* Create
* retrieve
* update
* and delete tasks.
### Comments on Tasks:
* Add 
* retrieve comments for tasks.


## Setup
Prerequisites,
Python 3.7 or higher,
Flask,
Flask-CORS,
Flask-PyMongo,
PyMongo,
bcrypt,
JWT,
Werkzeug

## Installation

### Clone the repository:

git clone <repository_url>
cd <repository_directory>

### Create a virtual environment:
python -m venv venv

### Activate the virtual environment:

#### On Windows:
venv\Scripts\activate


#### On macOS/Linux:
source venv/bin/activate

### Install the required packages:
pip install -r requirements.txt


### Add .env file with following details
SECRET_KEY=""  secret key details
MAIL_USERNAME=""     the sender mail for app
MAIL_PASSWORD=""    the password for the mail


### Run the application:
flask run


## The application will be available at http://127.0.0.1:5000/.

## Configuration
Install latest mongodb server 
MongoDB: The application is configured to connect to a MongoDB instance running on localhost:27017. Ensure that MongoDB is running and accessible.

