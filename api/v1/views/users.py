#!/usr/bin/env python3
"""This module handles all default RestFul API actions for Users"""
from flask import session, abort, jsonify, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from models.user import User
from models import storage
from models.artist import Artist
from models.news import News
from api.v1.views import app_views
from api.v1.views.news import invalidate_user_news_cache
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
        logger.info(f"Email already registered")
        return jsonify({"error": "Email already registered"}), 400

    # Ensure the new username is not already taken
    existing_user = storage.filter_by(User, username=username)
    if existing_user:
        logger.info(f"Username {username} already exists")
        return jsonify({"error": "Username already exists"}), 400

    # Create and save the new user
    user = User()
    user.username = username
    user.email = email
    user.password = password
    storage.new(user)
    storage.save()

    logger.info(f"New user registered")
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
        logger.warning(f"Failed login attempt for email")
        return jsonify({"error": "Invalid email or password"}), 401

    # Set user_id in session
    session['user_id'] = user.id
    logger.info(f"User logged in successfully")
    return jsonify({"message": "Logged in successfully", "userId": user.id}), 200


@app_views.route('/auth/logout', methods=['POST'], strict_slashes=False)
def logout() -> str:
    """Invalidate the user's session"""
    if 'user_id' in session:
        user_id = session['user_id']

        # Clear user-specific cache
        cache = current_app.cache
        cache.delete(f"user_profile:{user_id}")

        # Clear all potentially affected caches
        invalidate_user_news_cache(user_id)
        invalidate_all('album')
        invalidate_all('artist')
        invalidate_all('music')
        invalidate_all('playlist')
        invalidate_all('news')

        # Clear session
        session.clear()

        logger.info(f"User {user_id} logged out successfully.")
        return jsonify({"message": "Logged out successfully"}), 200

    logger.info("Logout attempt with no active session.")
    return jsonify({"error": "No active session"}), 400


@app_views.route('/users/me', methods=['GET'], strict_slashes=False)
def get_profile() -> str:
    """Retrieve the authenticated user's profile"""
    # Access cache within the route
    cache = current_app.cache

    # Check for user_id in session
    user_id = session.get('user_id')
    if not user_id:
        logger.info("Profile access attempt with no active session.")
        return jsonify({"error": "No active session"}), 401

    # Try to retrieve cached profile
    cache_key = f"user_profile:{user_id}"
    cached_profile = cache.get(cache_key)

    if cached_profile:
        logger.info(f"Returning cached profile for user {user_id}.")
        return cached_profile

    user = storage.get(User, user_id)

    if not user:
        logger.error(f"User {user_id} not found.")
        return jsonify({"error": "User not found"}), 404

    user_profile = jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture_url": user.profile_picture_url
        }
    })

    cache.set(cache_key, user_profile, timeout=3600)

    logger.info(f"User {user_id} retrieved their profile successfully.")
    return user_profile, 200


@app_views.route('/users/me', methods=['PUT'], strict_slashes=False)
def update_profile() -> str:
    """Update the authenticated user's profile (username only)"""
    user_id = session.get('user_id')

    if not user_id:
        logger.info("Unauthorized profile update attempt.")
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get('username')

    if not username or not isinstance(username, str) or username.strip() == "":
        logger.info(f"User {user_id} attempted to update profile with invalid username.")
        return jsonify({"error": "Valid username is required"}), 400, {'Content-Type': 'application/json'}

    if len(username) < 3 or len(username) > 30:
        logger.info(f"User {user_id} attempted to update profile with username of invalid length.")
        return jsonify({"error": "Username must be between 3 and 30 characters"}), 400

    if not username.isalnum():
        logger.info(f"User {user_id} attempted to update profile with non-alphanumeric username.")
        return jsonify({"error": "Username must contain only letters and numbers"}), 400

    user = storage.get(User, user_id)

    if not user:
        logger.error(f"User {user_id} not found during profile update.")
        return jsonify({"error": "User not found"}), 404

    # Ensure the new username is not already taken
    existing_user = storage.filter_by(User, username=username)
    if existing_user and existing_user.id != user_id:
        logger.info(f"User {user_id} attempted to use an already existing username: {username[:4]}***.")
        return jsonify({"error": "Username already exists"}), 400

    # Update username
    user.username = username
    storage.save()
    logger.info(f"User {user_id} updated their profile successfully.")
    current_app.cache.delete(f"user_profile:{user_id}")
    return jsonify({"message": "Profile updated successfully"}), 200


@app_views.route('/users/<string:user_id>', methods=['DELETE'], strict_slashes=False)
def delete_user(user_id: str) -> str:
    """Delete a user by ID and clear all associated caches"""
    if 'user_id' not in session:
        logger.warning("Unauthorized attempt to delete user without authentication.")
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    if session['user_id'] != user_id:
        logger.warning(f"User {session['user_id']} attempted to delete another user's account (ID: {user_id}).")
        return jsonify({"error": "Unauthorized. You can only delete your own account."}), 403

    user = storage.get(User, user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found.")
        return jsonify({"error": "User not found"}), 404

    try:
        cache = current_app.cache
        cache.delete(f"user_profile:{user_id}")
        logger.info(f"Cleared cache for user profile: {user_id}")

        # Clear all potentially affected caches
        invalidate_user_news_cache(user_id)
        invalidate_all('album')
        invalidate_all('artist')
        invalidate_all('music')
        invalidate_all('playlist')
        invalidate_all('news')

        session.clear()
        logger.info(f"Cleared session for user {user_id}")

        storage.delete(user)
        storage.save()

        logger.info(f"User with ID {user_id} deleted successfully.")
        return jsonify({"success": f"User {user_id} deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({"error": "An error occurred while deleting the user"}), 500


@app_views.route('/auth/reset-password', methods=['POST'], strict_slashes=False)
def request_password_reset() -> str:
    """Request a password reset by sending a token to the user's email."""
    email = request.form.get("email")

    if not email:
        logger.info("Password reset request with no email provided.")
        return jsonify({"error": "Email required"}), 400

    user = storage.filter_by(User, email=email)

    if not user:
        logger.error(f"Password reset request for non-existent email: {email[:4]}***@***.")
        return jsonify({"error": "User not found"}), 404

    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    storage.save()

    logger.info(f"Password reset token generated for {email[:4]}***@***.")
    return jsonify({"email": email, "reset_token": reset_token}), 200


@app_views.route('/auth/reset-password/confirm', methods=['POST'], strict_slashes=False)
def reset_password_with_token() -> str:
    """Redirect the user to change the password using the reset token."""
    token = request.form.get("token")

    if not token:
        logger.info("Password reset confirmation attempt with no token.")
        return jsonify({"error": "Missing fields"}), 400

    user = storage.filter_by(User, reset_token=token)

    if not user:
        logger.error(f"Invalid or expired token used: {token}.")
        return jsonify({"error": "Invalid or expired token"}), 400

    logger.info(f"Password reset confirmed for user with token: {token}.")
    return redirect(url_for('app_views.change_password', token=token))


@app_views.route('/auth/reset-password/change-password', methods=['POST'], strict_slashes=False)
def change_password() -> str:
    """Change the user's password after reset confirmation."""
    token = request.args.get("token")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not token or not new_password or not confirm_password:
        logger.info("Password change attempt with missing fields.")
        return jsonify({"error": "Missing fields"}), 400

    if new_password != confirm_password:
        logger.info("Password change attempt with non-matching passwords.")
        return jsonify({"error": "Passwords do not match"}), 400

    user = storage.filter_by(User, reset_token=token)

    if not user:
        logger.error(f"Password change failed with invalid token: {token}.")
        return jsonify({"error": "Invalid or expired token"}), 400

    try:
        setattr(user, "password", new_password)
        user.reset_token = None
        storage.save()
        logger.info(f"User {user.id} successfully changed their password.")
    except Exception as e:
        logger.error(f"Failed to update password for user {user.id}: {e}")
        return jsonify({"error": "Failed to update password"}), 500

    return jsonify({"message": "Password reset successfully"}), 200


@app_views.route('/users/me/profile-picture', methods=['POST'], strict_slashes=False)
def update_profile_picture() -> str:
    """Update the authenticated user's profile picture"""
    if 'user_id' not in session:
        logger.info("Profile picture update attempt with no active session.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    user = storage.get(User, user_id)

    if not user:
        logger.error(f"Profile picture update failed for non-existent user {user_id}.")
        return jsonify({"error": "User not found"}), 404

    file = request.files.get('file')
    if not file:
        logger.info(f"User {user_id} attempted to upload profile picture without a file.")
        return jsonify({"error": "No file uploaded"}), 400

    if request.content_length > MAX_CONTENT_LENGTH:
        logger.info(f"User {user_id} attempted to upload an oversized profile picture.")
        return jsonify({"error": "File is too large"}), 400

    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        logger.info(f"User {user_id} attempted to upload an invalid file type: {file_type}.")
        return jsonify({"error": "Invalid file type"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    file_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile{file_ext}")
    file.save(file_path)

    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile_thumbnail{file_ext}")
    try:
        image = Image.open(file_path)
        image.thumbnail((100, 100))
        image.save(thumbnail_path)
        logging.info(f"User {user_id} successfully updated their profile picture.")
    except Exception as e:
        logger.error(f"Error processing image for user {user_id}: {e}")
        return jsonify({"error": "Error processing image"}), 500

    user.profile_picture_url = thumbnail_path
    storage.save()

    # Invalidate cache for the user's profile
    current_app.cache.delete(f"user_profile:{user_id}")

    return jsonify({"message": "Profile picture updated successfully"}), 200


@app_views.route('/users/me/artists', methods=['GET'], strict_slashes=False)
def get_artists_by_user_id() -> str:
    """Retrieve artists associated with the authenticated user"""
    if 'user_id' not in session:
        logger.warning("Attempted to access artists with no active session.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning(f"Unauthorized access attempt by user {user_id}.")
        return jsonify({"error": "Unauthorized"}), 401

    # Retrieve all artists from storage
    all_artists = storage.all(Artist)
    user_artists = [artist for artist in all_artists if artist.user_id == user_id]

    if not user_artists:
        logger.info(f"No artists found for user {user_id}.")
        return jsonify({"artists": []}), 200

    logger.info(f"User {user_id} retrieved their artists successfully.")

    artist_list = [{"id": artist.id, "name": artist.name} for artist in user_artists]
    return jsonify({
        "artists": artist_list
    }), 200


@app_views.route('/users/me/news', methods=['GET'], strict_slashes=False)
def get_news_by_user_id() -> str:
    """Retrieve news articles associated with the authenticated user with caching"""
    if 'user_id' not in session:
        logger.warning("Attempted to access news with no active session.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning(f"Unauthorized access attempt by user {user_id}.")
        return jsonify({"error": "Unauthorized"}), 401

    # Pagination parameters
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # Generate cache key based on user ID and page
    cache_key = f"user_news:{user_id}:page_{page}"
    cached_news = current_app.cache.get(cache_key)

    if cached_news:
        logger.info(f"Returning cached news for user {user_id}, page {page}.")
        return cached_news

    # Retrieve all news for the authenticated user
    all_news = storage.all(News)
    user_news = [news for news in all_news if news.user_id == user_id]

    # Pagination logic
    total_count = len(user_news)
    start_index = (page - 1) * limit
    end_index = page * limit
    news_articles = user_news[start_index:end_index]

    if not news_articles:
        logger.info(f"No news articles found for user {user_id}.")
        response = jsonify({"news": [], "total": total_count, "page": page, "limit": limit}), 200
        current_app.cache.set(cache_key, response, timeout=3600)
        return response

    logger.info(f"User {user_id} retrieved their news articles successfully: page {page}, limit {limit}.")

    news_list = [
        {
            "id": news.id,
            "title": news.title
        } for news in news_articles
    ]

    response = jsonify({
        "news": news_list,
        "total": total_count,
        "page": page,
        "limit": limit
    }), 200

    # Cache the response with a timeout (e.g., 1 hour)
    current_app.cache.set(cache_key, response, timeout=3600)

    return response


def invalidate_all(model: str) -> None:
    """Invalidate all cache entries for a given model."""
    cache = current_app.cache
    patterns = [f"flask_cache_all_{model}*", f"flask_cache_{model}*"]
    
    for pattern in patterns:
        keys_to_delete = cache.cache._read_client.keys(pattern)
        if keys_to_delete:
            # Adjust the keys for deletion by removing any prefix if necessary
            adjusted_keys = [key.decode('utf-8').replace('flask_cache_', '', 1) for key in keys_to_delete]
            cache.delete_many(*adjusted_keys)
            logger.info(f"Invalidated {len(adjusted_keys)} cache entries for pattern: {pattern}")
        else:
            logger.info(f"No cache entries found to invalidate for pattern: {pattern}")
