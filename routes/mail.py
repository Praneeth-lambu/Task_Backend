import random
import string
from flask import Blueprint, current_app, jsonify, request
from flask_mail import Message
from datetime import datetime, timedelta

from utils.hashing import hash_password
from routes.users import get_user_management
from utils.validate.helpers import validate_user_data
mail_bp = Blueprint('mail', __name__)

# In-memory storage for OTPs with expiration
otp_store = {}  # Format: {email: (otp, timestamp)}
reset_token_store = {}

# Route to send OTP
@mail_bp.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Generate a random 6-digit OTP
    otp = random.randint(100000, 999999)
    
    # Create the email message
    msg = Message('Your OTP Code', sender=current_app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f'Your OTP code for Task app is {otp}'

    # Store OTP with current timestamp
    otp_store[email] = (otp, datetime.now())
    
    try:
        # Send the email
        current_app.extensions['mail'].send(msg)
        return jsonify({'message': 'OTP sent successfully'})
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send OTP'}), 500

# Route to verify OTP
@mail_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    email = request.json.get('email')
    user_otp = request.json.get('otp')
    
    if not email or not user_otp:
        return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400

    # Validate OTP format
    try:
        user_otp = int(user_otp)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid OTP format'}), 400
    # Fetch OTP and timestamp from store
    stored_otp, timestamp = otp_store.get(email, (None, None))
    current_time = datetime.now()
    
    ## Check if OTP exists and is within expiration time
    if stored_otp and stored_otp == user_otp:
        if current_time - timestamp < timedelta(minutes=5):  # 5-minute expiration
            del otp_store[email]  # Clear OTP after successful verification
            return jsonify({'success': True, 'message': 'OTP verified successfully'})
        else:
            return jsonify({'success': False, 'message': 'OTP expired'}), 400
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400
    
    # Route to request password reset
@mail_bp.route('/request_reset', methods=['POST'])
def request_reset():
    email = request.json.get('email')


    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    User_management = get_user_management()
    user = User_management.find_one({"email": email})

    if not user:
        return jsonify({'error':'No account found with that email Id please register'})


    # Generate a secure token for password reset
    reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # Create the email message
    reset_link = f'https://localhost:3000/reset?token={reset_token}'
    msg = Message('Password Reset Request', sender=current_app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f'Click the link below to reset your password:\n\n{reset_link}'

    # Store the reset token with current timestamp
    reset_token_store[reset_token] = (email, datetime.now())

    try:
        # Send the email
        current_app.extensions['mail'].send(msg)
        return jsonify({'message': 'Password reset email sent successfully'})
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send reset email'}), 500

@mail_bp.route('/reset_password', methods=['POST'])
def reset_password():
    token = request.json.get('token')
    new_password = request.json.get('password')
    print(token, new_password)
    
    if not token or not new_password:
        return jsonify({'msg': 'Token and new password are required'}), 400

    # Fetch token and timestamp from store
    stored_email, timestamp = reset_token_store.get(token, (None, None))
    current_time = datetime.now()
    print(stored_email, reset_token_store)

    # Check if token exists and is within expiration time
    if stored_email:
        if current_time - timestamp < timedelta(hours=1):  # 1-hour expiration
            # Remove the token after successful use
            del reset_token_store[token]
            
            # Fetch user details from the database using the email
            User_management = get_user_management()
            user = User_management.find_one({"email": stored_email})
            
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Extract the user's name
            name = user.get("name", "")
            
            # Validate the new password
            error_msg, status_code = validate_user_data(name=name, email=stored_email, password=new_password)
            if error_msg:
                return jsonify({'msg': error_msg}), status_code
            
            # Hash the new password
            hashed_password = hash_password(new_password)

            # Update the user's password in the database
            result = User_management.update_one(
                {"email": stored_email},
                {'$set': {"password": hashed_password}}
            )
            
            if result.matched_count > 0:
                return jsonify({'success': True, 'msg': 'Password reset successfully'}), 200
            else:
                return jsonify({'success': False, 'msg': 'Failed to update password'}), 500
        else:
            return jsonify({'success': False, 'msg': 'Reset token expired'}), 400
    else:
        return jsonify({'success': False, 'msg': 'Invalid token'}), 400