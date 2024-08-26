from flask import Blueprint, jsonify, request, current_app
from utils.hashing import hash_password, verify_password
from utils.validate.helpers import email_exists, validate_user_data
from utils.jwt_manager import encode_auth_token, decode_auth_token, token_required

home_bp = Blueprint('home', __name__)

@home_bp.route("/",methods=["GET"])
def home():
    return "<h1>Api Working</h1>"