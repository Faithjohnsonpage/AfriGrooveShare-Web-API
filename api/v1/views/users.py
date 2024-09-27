#!/usr/bin/env python3
"""This module handles all default RestFul API actions for Users"""
from flask import session, abort, jsonify, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from models.user import User
from models import storage
from api.v1.views import app_views
from PIL import Image
import os
import imghdr
import uuid
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('users.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


UPLOAD_FOLDER = 'api/v1/uploads/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


@app_views.route('/auth/register', methods=['POST'], strict_slashes=False)
def register() -> str:
    """Register a new user"""
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        logger.warning("Attempted registration with missing fields")
        return jsonify({"error": "Missing fields"}), 400
    
    # Check if the email is already registered
    if storage.exists(User, email=email):
        logger.info(f"Email {email[:4]}***@*** already registered")
        return jsonify({"error": "Email already registered"}), 400

    # Create and save the new user
    user = User()
    user.username = username
    user.email = email
    user.password = password
    storage.new(user)
    storage.save()

    logger.info(f"New user registered: ({email[:4]}***@***)")
    return jsonify({"message": "User registered successfully", "userId": user.id}), 201


@app_views.route('/auth/login', methods=['POST'], strict_slashes=False)
def login() -> str:
    """Authenticate a user and create a session"""
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not email or not password:
        logger.warning("Login attempt with missing fields")
        return jsonify({"error": "Missing fields"}), 400

    user = storage.filter_by(User, email=email)
    
    if not user or not user.verify_password(password):
        logger.warning(f"Failed login attempt for email: {email[:4]}***@***")
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Set user_id in session
    session['user_id'] = user.id
    logger.info(f"User logged in successfully")
    return jsonify({"message": "Logged in successfully", "userId": user.id}), 200


@app_views.route('/auth/logout', methods=['POST'], strict_slashes=False)
def logout() -> str:
    """Invalidate the user's session"""
    if 'user_id' in session:
        session.clear()
        logging.info(f"User {user_id} logged out successfully.")
        return jsonify({"message": "Logged out successfully"}), 200
    logging.info("Logout attempt with no active session.")
    return jsonify({"error": "No active session"}), 400


@app_views.route('/users/me', methods=['GET'], strict_slashes=False)
def get_profile() -> str:
    """Retrieve the authenticated user's profile"""
    if 'user_id' not in session:
        logging.info("Profile access attempt with no active session.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logging.error(f"User {user_id} not found.")
        return jsonify({"error": "Unauthorized"}), 401

    user = storage.get(User, user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    logging.info(f"User {user_id} retrieved their profile successfully.")
    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture_url": user.profile_picture_url
        }
    }), 200


@app_views.route('/users/me', methods=['PUT'], strict_slashes=False)
def update_profile() -> str:
    """Update the authenticated user's profile (username only)"""
    user_id = session.get('user_id')

    if not user_id:
        logging.info("Unauthorized profile update attempt.")
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get('username')
    
    if not username or username.strip() == "":
        logging.info(f"User {user_id} attempted to update profile with no username.")
        return jsonify({"error": "Username is required"}), 400

    user = storage.get(User, user_id)

    if not user:
        logging.error(f"User {user_id} not found during profile update.")
        return jsonify({"error": "User not found"}), 404

    # Ensure the new username is not already taken
    existing_user = storage.filter_by(User, username=username)
    if existing_user and existing_user.id != user_id:
        logging.info(f"User {user_id} attempted to use an already existing username: {username[:4]}***.")
        return jsonify({"error": "Username already exists"}), 400

    # Update username
    user.username = username
    storage.save()
    logging.info(f"User {user_id} updated their profile successfully.")
    return jsonify({"message": "Profile updated successfully"}), 200


@app_views.route('/auth/reset-password', methods=['POST'], strict_slashes=False)
def request_password_reset() -> str:
    """Request a password reset by sending a token to the user's email."""
    email = request.form.get("email")

    if not email:
        logging.info("Password reset request with no email provided.")
        return jsonify({"error": "Email required"}), 400

    user = storage.filter_by(User, email=email)

    if not user:
        logging.error(f"Password reset request for non-existent email: {email[:4]}***@***.")
        return jsonify({"error": "User not found"}), 404

    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    storage.save()

    logging.info(f"Password reset token generated for {email[:4]}***@***.")
    return jsonify({"email": email, "reset_token": reset_token}), 200


@app_views.route('/auth/reset-password/confirm', methods=['POST'], strict_slashes=False)
def reset_password_with_token() -> str:
    """Redirect the user to change the password using the reset token."""
    token = request.form.get("token")

    if not token:
        logging.info("Password reset confirmation attempt with no token.")
        return jsonify({"error": "Missing fields"}), 400

    user = storage.filter_by(User, reset_token=token)

    if not user:
        logging.error(f"Invalid or expired token used: {token}.")
        return jsonify({"error": "Invalid or expired token"}), 400

    logging.info(f"Password reset confirmed for user with token: {token}.")
    return redirect(url_for('app_views.change_password', token=token))


@app_views.route('/auth/reset-password/change-password', methods=['POST'], strict_slashes=False)
def change_password() -> str:
    """Change the user's password after reset confirmation."""
    token = request.args.get("token")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not token or not new_password or not confirm_password:
        logging.info("Password change attempt with missing fields.")
        return jsonify({"error": "Missing fields"}), 400
    
    if new_password != confirm_password:
        logging.info("Password change attempt with non-matching passwords.")
        return jsonify({"error": "Passwords do not match"}), 400

    user = storage.filter_by(User, reset_token=token)

    if not user:
        logging.error(f"Password change failed with invalid token: {token}.")
        return jsonify({"error": "Invalid or expired token"}), 400

    try:
        setattr(user, "password", new_password)
        user.reset_token = None
        storage.save()
        logging.info(f"User {user.id} successfully changed their password.")
    except Exception as e:
        logging.error(f"Failed to update password for user {user.id}: {e}")
        return jsonify({"error": "Failed to update password"}), 500

    return jsonify({"message": "Password reset successfully"}), 200


@app_views.route('/users/me/profile-picture', methods=['POST'], strict_slashes=False)
def update_profile_picture() -> str:
    """Update the authenticated user's profile picture"""
    if 'user_id' not in session:
        logging.info("Profile picture update attempt with no active session.")
        return jsonify({"error": "No active session"}), 401
    
    user_id = session.get('user_id')
    user = storage.get(User, user_id)
    
    if not user:
        logging.error(f"Profile picture update failed for non-existent user {user_id}.")
        return jsonify({"error": "User not found"}), 404

    file = request.files.get('file')
    if not file:
        logging.info(f"User {user_id} attempted to upload profile picture without a file.")
        return jsonify({"error": "No file uploaded"}), 400

    if request.content_length > MAX_CONTENT_LENGTH:
        logging.info(f"User {user_id} attempted to upload an oversized profile picture.")
        return jsonify({"error": "File is too large"}), 400

    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        logging.info(f"User {user_id} attempted to upload an invalid file type: {file_type}.")
        return jsonify({"error": "Invalid file type"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile.jpg")
    file.save(file_path)

    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile_thumbnail.jpg")
    try:
        image = Image.open(file_path)
        image.thumbnail((100, 100))
        image.save(thumbnail_path)
        logging.info(f"User {user_id} successfully updated their profile picture.")
    except Exception as e:
        logging.error(f"Error processing image for user {user_id}: {e}")
        return jsonify({"error": "Error processing image"}), 500

    user.profile_picture_url = thumbnail_path
    storage.save()

    return jsonify({"message": "Profile picture updated successfully"}), 200
