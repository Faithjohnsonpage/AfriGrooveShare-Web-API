#!/usr/bin/env python3
"""This module handles all admin-related API actions"""
from flask import jsonify, request, session, current_app
from models import storage
from models.user import User
from models.artist import Artist
from models.album import Album
from models.genre import Genre
from models.admin import Admin
from models.music import Music, ReleaseType
from models.news import News
from api.v1.views import app_views
import logging
from functools import wraps
from api.v1.views.users import invalidate_all


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('admin.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def admin_required(func):
    """Decorator to check if the user is an admin"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            logger.warning("Unauthorized access attempt to admin route.")
            return jsonify({"error": "Unauthorized"}), 401

        user = storage.get(User, user_id)
        admin = storage.filter_by(Admin, user_id=user_id)

        if not user or not admin:
            logger.warning(f"Non-admin user {user_id} attempted to access admin route.")
            return jsonify({"error": "Admin privileges required"}), 403
        
        return func(*args, **kwargs)
    return wrapper


@app_views.route('/admin/users', methods=['GET'], strict_slashes=False)
@admin_required
def get_all_users():
    """Retrieve all users"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    users = storage.all(User)

    # Pagination
    total_count = len(users)
    start_index = (page - 1) * limit
    end_index = page * limit
    paginated_users = users[start_index:end_index]

    # Process paginated users only
    users_list = [{"id": user.id, "username": user.username, "email": user.email} for user in paginated_users]

    logger.info("Admin retrieved all users successfully.")

    return jsonify({
        "users": users_list,
        "total_count": total_count,
        "page": page,
        "limit": limit
    }), 200


@app_views.route('/admin/users/<string:user_id>', methods=['DELETE'], strict_slashes=False)
@admin_required
def admin_delete_user(user_id: str) -> str:
    """Delete a user (admin action)"""
    user = storage.get(User, user_id)
    if not user:
        logger.warning(f"Admin attempted to delete non-existent user {user_id}.")
        return jsonify({"error": "User not found"}), 404

    storage.delete(user)
    storage.save()
    logger.info(f"Admin deleted user {user_id} successfully.")
    return jsonify({"message": "User deleted successfully"}), 200


@app_views.route('/admin/artists/<string:artist_id>', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_artist_by_admin(artist_id: str) -> str:
    """Delete an artist"""
    artist = storage.get(Artist, artist_id)
    if not artist:
        logger.warning(f"Admin attempted to delete non-existent artist {artist_id}.")
        return jsonify({"error": "Artist not found"}), 404

    storage.delete(artist)
    storage.save()

    try:
        invalidate_all('artist')
    except Exception as e:
        logger.error(f"Error invalidating cache for artists: {str(e)}")

    logger.info(f"Admin deleted artist {artist_id} successfully.")
    return jsonify({"message": "Artist deleted successfully"}), 200


@app_views.route('/admin/albums/<string:album_id>', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_album(album_id: str) -> str:
    """Delete an album"""
    album = storage.get(Album, album_id)
    if not album:
        logger.warning(f"Admin attempted to delete non-existent album {album_id}.")
        return jsonify({"error": "Album not found"}), 404

    storage.delete(album)
    storage.save()

    try:
        invalidate_all('album')
    except Exception as e:
        logger.error(f"Error invalidating cache for albums: {str(e)}")

    logger.info(f"Admin deleted album {album_id} successfully.")
    return jsonify({"message": "Album deleted successfully"}), 200


@app_views.route('/admin/list', methods=['GET'], strict_slashes=False)
@admin_required
def get_all_admins() -> str:
    """Retrieve list of all admins"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    admins = storage.all(Admin)

    # Pagination
    total_count = len(admins)
    start_index = (page - 1) * limit
    end_index = page * limit
    paginated_admins = admins[start_index:end_index]
    
    admins_list = []
    for admin in paginated_admins:
        user = storage.filter_by(User, id=admin.user_id)
        if user:
            admins_list.append({
                "id": admin.id,
                "username": user.username,
                "email": user.email
            })

    logger.info("Admin retrieved all admins successfully.")

    return jsonify({
        "admins": admins_list,
        "total_count": total_count,
        "page": page,
        "limit": limit
    }), 200


@app_views.route('/admin/music/<string:music_id>', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_single(music_id: str) -> str:
    """Delete a single music item or return an error if it's an album."""

    music = storage.get(Music, music_id)
    if not music:
        logger.warning(f"Admin attempted to delete non-existent music {music_id}.")
        return jsonify({"error": "Music not found"}), 404

    if music.release_type == ReleaseType.ALBUM:
        logger.warning(f"Admin attempted to delete an album {music_id}.")
        return jsonify({"error": "Cannot delete an album"}), 403

    storage.delete(music)
    storage.save()

    try:
        invalidate_all('music')
    except Exception as e:
        logger.error(f"Error invalidating cache for music: {str(e)}")

    logger.info(f"Admin deleted single {music_id} successfully.")
    return jsonify({"message": "Single deleted successfully"}), 200


#@app_views.route('/admin/users/<string:user_id>/block', methods=['PUT'], strict_slashes=False)
#@admin_required
#def block_user(user_id: str) -> str:
#    """Block a user (admin action)"""
#    user = storage.get(User, user_id)
#    if not user:
#        logger.warning(f"Admin attempted to block non-existent user {user_id}.")
#        return jsonify({"error": "User not found"}), 404
#
#    user.is_blocked = True
#    storage.save()
#    logger.info(f"Admin blocked user {user_id} successfully.")
#    return jsonify({"message": "User blocked successfully"}), 200


#@app_views.route('/admin/users/<string:user_id>/unblock', methods=['PUT'], strict_slashes=False)
#@admin_required
#def unblock_user(user_id: str) -> str:
#    """Unblock a user (admin action)"""
#    user = storage.get(User, user_id)
#    if not user:
#        logger.warning(f"Admin attempted to unblock non-existent user {user_id}.")
#        return jsonify({"error": "User not found"}), 404
#
#    user.is_blocked = False
#    storage.save()
#    logger.info(f"Admin unblocked user {user_id} successfully.")
#    return jsonify({"message": "User unblocked successfully"}), 200


@app_views.route('/admin/news/<string:news_id>', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_news_article(news_id: str) -> str:
    """Delete a news article"""
    news_article = storage.get(News, news_id)
    if not news_article:
        logger.warning(f"Admin attempted to delete non-existent news article {news_id}.")
        return jsonify({"error": "News article not found"}), 404

    storage.delete(news_article)
    storage.save()

    try:
        invalidate_all('news')
    except Exception as e:
        logger.error(f"Error invalidating cache for news: {str(e)}")

    logger.info(f"Admin deleted news article {news_id} successfully.")
    return jsonify({"message": "News article deleted successfully"}), 200


@app_views.route('/admin/news/review', methods=['GET'], strict_slashes=False)
@admin_required
def get_news_for_review() -> str:
    """Retrieve news posts that need admin review before going live"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # Fetch all news articles with status 'live' from storage
    all_news = storage.all(News)
    pending_news = [news for news in all_news if news.reviewed == False]

    # Pagination
    total_count = len(pending_news)
    start_index = (page - 1) * limit
    end_index = page * limit
    paginated_news = pending_news[start_index:end_index]

    news_for_review = [
        {
            "id": news.id,
            "title": news.title,
            "author_id": news.user_id,
            "created_at": news.created_at.isoformat()
        } for news in paginated_news
    ]

    # Include pagination metadata
    response = {
        "pending_news": news_for_review,
        "total": total_count,
        "page": page,
        "limit": limit
    }

    logger.info(f"Admin retrieved {len(news_for_review)} news posts for review (page {page}).")
    return jsonify(response), 200


@app_views.route('/admin/news/<string:news_id>/review', methods=['POST'], strict_slashes=False)
@admin_required
def review_news(news_id: str) -> str:
    """Review a specific news post"""
    
    news = storage.get(News, news_id)
    if not news:
        logger.warning(f"Admin attempted to review non-existent news with id {news_id}")
        return jsonify({"error": "News post not found"}), 404

    action = request.json.get('action')
    if action not in ['approve', 'reject']:
        logger.warning(f"Admin provided invalid action '{action}' for news review")
        return jsonify({"error": "Invalid action. Use 'approve' or 'reject'"}), 400

    # Apply review decision
    if action == 'approve':
        news.reviewed = True
        logger.info(f"Admin approved news post {news_id}")
    else:
        news.status = 'private'
        news.reviewed = True
        logger.info(f"Admin rejected news post {news_id}")

    storage.save()
    return jsonify({"message": f"News post {action}d successfully"}), 200


@app_views.route('/admin/genres', methods=['POST'], strict_slashes=False)
@admin_required
def add_genre() -> str:
    """Add a new genre"""
    name = request.json.get('name')
    if not name:
        logger.warning("Admin attempted to add a genre without a name.")
        return jsonify({"error": "Genre name is required"}), 400

    existing_genre = storage.filter_by(Genre, name=name)
    if existing_genre:
        logger.warning(f"Admin attempted to add an existing genre: {name}.")
        return jsonify({"error": "Genre already exists"}), 400

    genre = Genre()
    genre.name = name
    storage.new(genre)
    storage.save()

    logger.info(f"Admin added new genre: {name}.")
    return jsonify({"message": "Genre added successfully", "id": genre.id}), 201


@app_views.route('/admin/genres/<string:genre_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def update_genre(genre_id: str) -> str:
    """Update a genre"""
    genre = storage.get(Genre, genre_id)
    if not genre:
        logger.warning(f"Admin attempted to update non-existent genre {genre_id}.")
        return jsonify({"error": "Genre not found"}), 404

    name = request.json.get('name')
    if not name:
        logger.warning("Admin attempted to update a genre without providing a name.")
        return jsonify({"error": "Genre name is required"}), 400

    genre.name = name
    storage.save()
    logger.info(f"Admin updated genre {genre_id} to: {name}.")
    return jsonify({"message": "Genre updated successfully"}), 200


@app_views.route('/admin/genres/<string:genre_id>', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_genre(genre_id: str) -> str:
    """Delete a genre"""
    genre = storage.get(Genre, genre_id)
    if not genre:
        logger.warning(f"Admin attempted to delete non-existent genre {genre_id}.")
        return jsonify({"error": "Genre not found"}), 404

    storage.delete(genre)
    storage.save()
    logger.info(f"Admin deleted genre {genre_id} successfully.")
    return jsonify({"message": "Genre deleted successfully"}), 200


# Remove or comment out the config management and security logs routes
# @app_views.route('/admin/config', methods=['GET', 'PUT'], strict_slashes=False)
# @admin_required
# def manage_config():
#     ...

# @app_views.route('/admin/security/logs', methods=['GET'], strict_slashes=False)
# @admin_required
# def get_security_logs():
#     ...

#@app_views.route('/admin/backup', methods=['POST'], strict_slashes=False)
#@admin_required
#def initiate_backup():
#    ...

#@app_views.route('/admin/restore', methods=['POST'], strict_slashes=False)
#@admin_required
#def restore_backup():
#    ...
