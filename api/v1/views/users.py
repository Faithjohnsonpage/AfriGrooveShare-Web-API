#!/usr/bin/env python3
"""This module handles all default RestFul API actions for Users"""
from flask import session, abort, jsonify, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from models.user import User
from models import storage
from api.v1.views import app_views
from typing import Dict, Any
from PIL import Image
import os
import imghdr
import uuid


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
        return jsonify({"error": "Missing fields"}), 400
    
    # Check if the email is already registered
    if storage.exists(User, email=email):
        return jsonify({"error": "Email already registered"}), 400

    # Create and save the new user
    user = User()
    user.username = username
    user.email = email
    user.password = password
    storage.new(user)
    storage.save()

    return jsonify({"message": "User registered successfully", "userId": user.id}), 201


@app_views.route('/auth/login', methods=['POST'], strict_slashes=False)
def login() -> str:
    """Authenticate a user and create a session"""
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    user = storage.filter_by(User, email=email)
    
    if not user or not user.verify_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Set user_id in session
    session['user_id'] = user.id
    return jsonify({"message": "Logged in successfully", "userId": user.id}), 200


@app_views.route('/auth/logout', methods=['POST'], strict_slashes=False)
def logout() -> str:
    """Invalidate the user's session"""
    if 'user_id' in session:
        session.clear()
        return jsonify({"message": "Logged out successfully"}), 200
    return jsonify({"error": "No active session"}), 400


@app_views.route('/users/me', methods=['GET'], strict_slashes=False)
def get_profile() -> str:
    """Retrieve the authenticated user's profile"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = storage.get(User, user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
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
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get('username')
    
    if not username or username.strip() == "":
        return jsonify({"error": "Username is required"}), 400

    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Ensure the new username is not already taken
    existing_user = storage.filter_by(User, username=username)
    if existing_user and existing_user.id != user_id:
        return jsonify({"error": "Username already exists"}), 400

    # Update username
    user.username = username
    storage.save()

    return jsonify({"message": "Profile updated successfully"}), 200


@app_views.route('/auth/reset-password', methods=['POST'], strict_slashes=False)
def request_password_reset() -> str:
    """Request a password reset by sending a token to the user's email."""
    email = request.form.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = storage.filter_by(User, email=email)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Generate a reset token
    reset_token = str(uuid.uuid4())

    user.reset_token = reset_token
    storage.save()

    return jsonify({"email": email, "reset_token": reset_token}), 200


@app_views.route('/auth/reset-password/confirm', methods=['POST'], strict_slashes=False)
def reset_password_with_token() -> str:
    """Redirect the user to change the password using the reset token."""
    token = request.form.get("token")
    
    if not token:
        return jsonify({"error": "Missing fields"}), 400

    user = storage.filter_by(User, reset_token=token)
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400

    # Redirect to the change-password route
    return redirect(url_for('app_views.change_password', token=token))


@app_views.route('/auth/reset-password/change-password', methods=['POST'], strict_slashes=False)
def change_password() -> str:
    """Change the user's password after reset confirmation."""
    token = request.args.get("token")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not token or not new_password or not confirm_password:
        return jsonify({"error": "Missing fields"}), 400
    
    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    # Find user by reset token
    user = storage.filter_by(User, reset_token=token)
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400

    try:
        setattr(user, "password", new_password)
        user.reset_token = None
        storage.save()
    except Exception as e:
        return jsonify({"error": "Failed to update password"}), 500

    return jsonify({"message": "Password reset successfully"}), 200


@app_views.route('/users/me/profile-picture', methods=['POST'], strict_slashes=False)
def update_profile_picture() -> str:
    """Update the authenticated user's profile picture"""
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401
    
    user_id = session.get('user_id')
    user = storage.get(User, user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if the file is in the request
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Check if the file size is within the limit
    if request.content_length > MAX_CONTENT_LENGTH:
        return jsonify({"error": "File is too large"}), 400

    # Check the file's signature (magic number)
    file_type = imghdr.what(file)
    print(file_type)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file type"}), 400

    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Save the original image securely
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile.jpg")
    file.save(file_path)

    # Generate a thumbnail for the profile picture
    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile_thumbnail.jpg")
    try:
        image = Image.open(file_path)
        image.thumbnail((100, 100))  # Create a 100x100 thumbnail
        image.save(thumbnail_path)
    except Exception as e:
        return jsonify({"error": "Error processing image"}), 500

    # Update the user profile picture URL
    user.profile_picture_url = thumbnail_path
    storage.save()

    return jsonify({"message": "Profile picture updated successfully"}), 200
