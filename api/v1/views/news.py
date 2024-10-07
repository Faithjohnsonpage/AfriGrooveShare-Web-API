#!/usr/bin/env python3
from flask import jsonify, request, session, current_app
from models import storage
from models.news import News
from models.user import User
from api.v1.views import app_views
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('news.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


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

    logger.info(f"News article '{title}' created successfully by user '{user.username}'.")
    return jsonify({"message": "News created successfully", "newsId": news.id}), 201


@app_views.route('/news/<string:news_id>', methods=['GET'], strict_slashes=False)
def get_news(news_id: str) -> str:
    """Retrieve a news article by ID"""
    
    cache_key = f"news_{news_id}"
    cached_news = current_app.cache.get(cache_key)
    
    if cached_news:
        logger.info(f"Serving cached news article {news_id}.")
        return cached_news, 200
    
    news = storage.get(News, news_id)
    if not news:
        logger.warning(f"News article with ID {news_id} not found.")
        return jsonify({"error": "News not found"}), 404

    response = jsonify({
        "news": {
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "publicationDate": str(news.created_at)
        }
    })
    
    current_app.cache.set(cache_key, response, timeout=3600)
    logger.info(f"News article with ID {news_id} retrieved and cached successfully.")
    
    return response, 200


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
    logger.info(f"Invalidated cache for news {news_id}")

    logger.info(f"News article with ID {news_id} updated successfully.")
    return jsonify({"message": "News updated successfully"}), 200


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
    logger.info(f"Invalidated cache for news {news_id}")

    logger.info(f"News article with ID {news_id} deleted successfully.")
    return jsonify({"message": "News deleted successfully"}), 200


@app_views.route('/news', methods=['GET'], strict_slashes=False)
def list_news() -> str:
    """List all news articles with caching"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # Cache key based on the page and limit
    cache_key = f"all_news:page_{page}_limit_{limit}"
    
    # Try fetching from cache first
    cached_news = current_app.cache.get(cache_key)
    if cached_news:
        logger.info(f"Returning cached news for page {page}, limit {limit}.")
        return jsonify(cached_news), 200

    # If not in cache, get data from storage
    news = storage.all(News)

    # Pagination
    total_count = len(news)
    start_index = (page - 1) * limit
    end_index = page * limit
    news_articles = news[start_index:end_index]

    response_data = {
        "news": [
            {
                "id": news.id,
                "title": news.title,
                "content": news.content,
                "category": news.category,
                "publicationDate": str(news.created_at)
            } for news in news_articles
        ],
        "total": total_count,
        "page": page,
        "limit": limit
    }

    # Cache the response data
    current_app.cache.set(cache_key, response_data, timeout=3600)
    logger.info(f"News articles cached for page {page}, limit {limit}.")
    
    return jsonify(response_data), 200


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
