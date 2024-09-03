import random
from flask import Blueprint, current_app, jsonify, request
from flask_mail import Message
from datetime import datetime, timedelta

mail_bp = Blueprint('mail', __name__)

# In-memory storage for OTPs with expiration
otp_store = {}  # Format: {email: (otp, timestamp)}

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
        return jsonify({'error': 'Email and OTP are required'}), 400
    
    # Fetch OTP and timestamp from store
    stored_otp, timestamp = otp_store.get(email, (None, None))
    current_time = datetime.now()
    
    # Check if OTP exists and is within expiration time
    if stored_otp and stored_otp == user_otp:
        if current_time - timestamp < timedelta(minutes=5):  # 5-minute expiration
            del otp_store[email]  # Clear OTP after successful verification
            return jsonify({'message': 'OTP verified successfully'})
        else:
            return jsonify({'error': 'OTP expired'}), 400
    else:
        return jsonify({'error': 'Invalid OTP'}), 400
