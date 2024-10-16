#!/usr/bin/env python3
from flask import jsonify, request, session, current_app, url_for
from models import storage
from models.news import News
from models.user import User
from models.news_image import NewsImage
from api.v1.views import app_views
import logging
from werkzeug.utils import secure_filename
from PIL import Image
import imghdr
import os
import uuid
from math import ceil


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('news.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


UPLOAD_FOLDER = 'api/v1/uploads/news_cover'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


@app_views.route('/news', methods=['POST'], strict_slashes=False)
def create_news() -> str:
    """Create a news article"""
    if 'user_id' not in session:
        logger.warning("No active session during news creation attempt.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    user = storage.get(User, user_id)

    if not user:
        logger.error(f"User with ID {user_id} not found during news creation.")
        return jsonify({"error": "User not found"}), 404

    allowed_music_categories = [
        'Album Release', 'Single Release', 'Artist News', 'Concerts & Tours',
        'Music Awards', 'Music Charts', 'Music Reviews', 'Collaborations',
        'Music Trends', 'Behind the Scenes', 'Music Festivals',
        'New Artist Spotlight', 'Music Technology'
    ]

    title = request.form.get('title')
    content = request.form.get('content')
    category = request.form.get('category')

    if category and category not in allowed_music_categories:
        logger.warning(f"Invalid category '{category}' during news creation.")
        return jsonify({"error": "Invalid category"}), 400

    if not title or not content:
        logger.warning("Missing title or content during news creation.")
        return jsonify({"error": "Missing title or content"}), 400

    #if len(content.split()) < 500:
        #return jsonify({"error": "Content must be at least 500 words."}), 400

    news = News()
    news.title = title
    news.content = content
    news.category = category if category else None
    news.author = user.username
    news.user_id = user_id
    storage.new(news)
    storage.save()

    # Invalidate the user's news cache
    invalidate_user_news_cache(user_id)

    # Invalidate all news cache
    invalidate_all_news_cache()

    logger.info(f"News article '{title}' created successfully.")

    response_data = {
        "message": "News created successfully",
        "newsId": news.id,
        "_links": {
            "self": {"href": url_for("app_views.get_news", news_id=news.id, _external=True)},
            "update": {"href": url_for("app_views.update_news", news_id=news.id, _external=True)},
            "delete": {"href": url_for("app_views.delete_news", news_id=news.id, _external=True)},
            "upload_image": {"href": url_for("app_views.upload_news_image", news_id=news.id, _external=True)},
            "all_news": {"href": url_for("app_views.list_news", _external=True)}
        }
    }

    return jsonify(response_data), 201


@app_views.route('/news/<string:news_id>', methods=['GET'], strict_slashes=False)
def get_news(news_id: str) -> str:
    """Retrieve a news article by ID"""

    # Get current user ID (if authenticated)
    current_user_id = session.get('user_id')

    # Check if the news is cached
    if current_user_id:
        cache_key = f"news_{news_id}_user_{current_user_id}"
    else:
        cache_key = f"news_{news_id}"
    cached_news = current_app.cache.get(cache_key)
    
    if cached_news:
        logger.info(f"Serving cached news article {news_id}.")
        return cached_news, 200
    
    news = storage.get(News, news_id)
    if not news:
        logger.warning(f"News article with ID {news_id} not found.")
        return jsonify({"error": "News not found"}), 404

    # Retrieve all related images from the NewsImage table
    news_images = storage.all(NewsImage)
    img_urls = [
        f"{request.host_url}static/{img.image_url}" 
        for img in news_images if img.news_id == news.id
    ]

    response_data = {
        "news": {
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "publicationDate": str(news.created_at),
            "status": news.status,
            "reviewed": news.reviewed,
            "images": img_urls,
            "_links": {
                "self": {"href": url_for("app_views.get_news", news_id=news.id, _external=True)},
                "all_news": {"href": url_for("app_views.list_news", _external=True)}
            }
        }
    }

    if current_user_id and news.user_id == current_user_id:
        response_data["news"]["_links"].update({
            "update": {"href": url_for("app_views.update_news", news_id=news.id, _external=True)},
            "delete": {"href": url_for("app_views.delete_news", news_id=news.id, _external=True)},
            "upload_image": {"href": url_for("app_views.upload_news_image", news_id=news.id, _external=True)}
        })

    current_app.cache.set(cache_key, response_data, timeout=3600)
    logger.info(f"News article with ID {news_id} retrieved and cached successfully.")
    
    return response_data, 200


@app_views.route('/news/<string:news_id>', methods=['PUT'], strict_slashes=False)
def update_news(news_id: str) -> str:
    """Update a news article by ID"""
    if 'user_id' not in session:
        logger.warning("No active session during news update attempt.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning(f"Unauthorized user with ID {user_id} attempted to update news.")
        return jsonify({"error": "Unauthorized"}), 401

    news = storage.get(News, news_id)
    if not news:
        logger.error(f"News article with ID {news_id} not found for update.")
        return jsonify({"error": "News not found"}), 404

    data = request.get_json()
    if data.get("title"):
        news.title = data["title"]
    if data.get("content"):
        news.content = data["content"]

    storage.save()

    # Invalidate the user's news cache
    invalidate_user_news_cache(user_id)

    # Invalidate all news cache
    invalidate_all_news_cache()

    current_app.cache.delete(f"news_{news_id}")
    current_app.cache.delete(f"news_{news_id}_user_{user_id}")
    logger.info(f"Invalidated cache for news {news_id}")

    logger.info(f"News article with ID {news_id} updated successfully.")

    response_data = {
        "message": "News updated successfully",
        "_links": {
            "self": {"href": url_for("app_views.get_news", news_id=news_id, _external=True)},
            "delete": {"href": url_for("app_views.delete_news", news_id=news_id, _external=True)},
            "upload_image": {"href": url_for("app_views.upload_news_image", news_id=news_id, _external=True)},
            "all_news": {"href": url_for("app_views.list_news", _external=True)}
        }
    }

    return jsonify(response_data), 200


@app_views.route('/news/<string:news_id>', methods=['DELETE'], strict_slashes=False)
def delete_news(news_id: str) -> str:
    """Delete a news article by ID"""
    if 'user_id' not in session:
        logger.warning("No active session during news deletion attempt.")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning(f"Unauthorized user with ID {user_id} attempted to delete news.")
        return jsonify({"error": "Unauthorized"}), 401

    news = storage.get(News, news_id)
    if not news:
        logger.error(f"News article with ID {news_id} not found for deletion.")
        return jsonify({"error": "News not found"}), 404

    storage.delete(news)
    storage.save()

    # Invalidate the user's news cache
    invalidate_user_news_cache(user_id)

    # Invalidate all news cache
    invalidate_all_news_cache()

    current_app.cache.delete(f"news_{news_id}")
    current_app.cache.delete(f"news_{news_id}_user_{user_id}")
    logger.info(f"Invalidated cache for news {news_id}")

    logger.info(f"News article with ID {news_id} deleted successfully.")

    response_data = {
        "message": "News deleted successfully",
        "_links": {
            "create_news": {"href": url_for("app_views.create_news", _external=True)},
            "all_news": {"href": url_for("app_views.list_news", _external=True)}
        }
    }

    return jsonify(response_data), 200


@app_views.route('/news', methods=['GET'], strict_slashes=False)
def list_news() -> str:
    """List all news articles with caching"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # Get current user ID (if authenticated)
    current_user_id = session.get('user_id')

    # Create different cache keys for authenticated and non-authenticated users
    if current_user_id:
        cache_key = f"all_news:page_{page}_limit_{limit}_user_{current_user_id}"
    else:
        cache_key = f"all_news:page_{page}_limit_{limit}"    
    cached_news = current_app.cache.get(cache_key)

    if cached_news:
        logger.info(f"Returning cached news for page {page}, limit {limit}.")
        return jsonify(cached_news), 200

    # Fetch all news articles with status 'live' from storage
    all_news = storage.all(News)
    live_news = [news for news in all_news if news.status == 'live']

    # Pagination
    total_count = len(live_news)
    start_index = (page - 1) * limit
    end_index = page * limit
    news_articles = live_news[start_index:end_index]

    # Build news articles list with appropriate links based on authentication
    news_list = []
    for news in news_articles:
        news_data = {
            "id": news.id,
            "title": news.title,
            "category": news.category,
            "publicationDate": str(news.created_at),
            "_links": {
                "self": {"href": url_for("app_views.get_news", news_id=news.id, _external=True)}
            }
        }
        
        # Add management links only if user is authenticated and owns the news
        if current_user_id and news.user_id == current_user_id:
            news_data["_links"].update({
                "update": {"href": url_for("app_views.update_news", news_id=news.id, _external=True)},
                "delete": {"href": url_for("app_views.delete_news", news_id=news.id, _external=True)},
                "upload_image": {"href": url_for("app_views.upload_news_image", news_id=news.id, _external=True)}
            })
        
        news_list.append(news_data)

    # Build base response with navigation links
    response_data = {
        "news": news_list,
        "total": total_count,
        "page": page,
        "limit": limit,
        "_links": {
            "self": {"href": url_for("app_views.list_news", page=page, limit=limit, _external=True)},
            "first": {"href": url_for("app_views.list_news", page=1, limit=limit, _external=True)},
            "last": {"href": url_for("app_views.list_news", page=ceil(total_count/limit), limit=limit, _external=True)},
            "next": {"href": url_for("app_views.list_news", page=page+1, limit=limit, _external=True)} if page * limit < total_count else None,
            "prev": {"href": url_for("app_views.list_news", page=page-1, limit=limit, _external=True)} if page > 1 else None
        }
    }

    # Add create_news link only for authenticated users
    if current_user_id:
        response_data["_links"]["create_news"] = {
            "href": url_for("app_views.create_news", _external=True)
        }

    # Cache the response data
    current_app.cache.set(cache_key, response_data, timeout=3600)
    logger.info(f"News articles cached for page {page}, limit {limit}.")
    
    return jsonify(response_data), 200


@app_views.route('/news/<string:news_id>/image', methods=['POST'], strict_slashes=False)
def upload_news_image(news_id: str) -> str:
    """Upload an image for a news article"""
    logger.info(f"Attempting to upload image for news article with ID {news_id}")

    if 'user_id' not in session:
        logger.warning("No active session for image upload")
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        logger.warning("Unauthorized image upload attempt")
        return jsonify({"error": "Unauthorized"}), 401

    news = storage.get(News, news_id)
    if not news:
        logger.error(f"News article with ID {news_id} not found")
        return jsonify({"error": "News article not found"}), 404

    # Check if the file is in the request
    file = request.files.get('file')
    if not file:
        logger.warning(f"No file uploaded for news article {news_id} image upload")
        return jsonify({"error": "No file uploaded"}), 400

    # Check if the file size is within the limit
    if request.content_length > MAX_CONTENT_LENGTH:
        logger.warning(f"File too large for news article {news_id} image upload")
        return jsonify({"error": "File is too large"}), 400

    # Check the file's signature (magic number)
    file_type = imghdr.what(file)
    if not file_type or file_type not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file type for news article {news_id} image upload")
        return jsonify({"error": f"Invalid file type. Supported types: {ALLOWED_EXTENSIONS}"}), 400

    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Generate a unique filename
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{news_id}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(file_path)

    # Save the image URL to the database
    news_image = NewsImage()
    news_image.news_id = news_id
    news_image.image_url = file_path
    storage.new(news_image)
    storage.save()

    # Invalidate the user's news cache
    invalidate_user_news_cache(user_id)

    # Invalidate all news cache
    invalidate_all_news_cache()

    current_app.cache.delete(f"news_{news_id}")
    current_app.cache.delete(f"news_{news_id}_user_{user_id}")
    logger.info(f"Invalidated cache for news {news_id}")

    logger.info(f"Image uploaded successfully for news article {news_id}")

    response_data = {
        "message": "Image uploaded successfully",
        "_links": {
            "news": {"href": url_for("app_views.get_news", news_id=news_id, _external=True)},
            "update_news": {"href": url_for("app_views.update_news", news_id=news_id, _external=True)},
            "delete_news": {"href": url_for("app_views.delete_news", news_id=news_id, _external=True)},
            "all_news": {"href": url_for("app_views.list_news", _external=True)}
        }
    }


def invalidate_user_news_cache(user_id):
    """Invalidate all cache entries for a user's news"""
    cache = current_app.cache
    pattern = f"flask_cache_user_news:{user_id}:page_*"

    # Get all keys matching the pattern (keys are returned as bytes)
    keys_to_delete = [
        key.decode('utf-8') for key in cache.cache._read_client.keys(pattern)
    ]

    # Remove the 'flask_cache_' prefix only when deleting
    if keys_to_delete:
        keys_for_deletion = [key.replace('flask_cache_', '', 1) for key in keys_to_delete]
        cache.delete_many(*keys_for_deletion)
        logger.info(f"Invalidated {len(keys_for_deletion)} cache entries for user {user_id}")
    else:
        logger.info(f"No cache entries found to invalidate for user {user_id}")


def invalidate_all_news_cache():
    """Invalidate all cache entries related to news."""
    cache = current_app.cache
    pattern = "flask_cache_all_news:page_*"

    # Get all keys matching the pattern
    keys_to_delete = [key.decode('utf-8') for key in cache.cache._read_client.keys(pattern)]

    if keys_to_delete:
        # Adjust the keys for deletion by removing any prefix if necessary
        adjusted_keys = [key.replace('flask_cache_', '', 1) for key in keys_to_delete]
        cache.delete_many(*adjusted_keys)
        logger.info(f"Invalidated {len(adjusted_keys)} cache entries for all news")
    else:
        logger.info("No cache entries found to invalidate for all news")
