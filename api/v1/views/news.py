#!/usr/bin/env python3
from flask import jsonify, request, session
from models import storage
from models.news import News
from models.user import User
from api.v1.views import app_views


@app_views.route('/news', methods=['POST'], strict_slashes=False)
def create_news():
    """Create a news article"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    user = storage.get(User, user_id)

    if not user:
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
        return jsonify({"error": "Invalid category"}), 400

    if not title or not content:
        return jsonify({"error": "Missing title or content"}), 400

    news = News()
    news.title = title
    news.content = content
    news.category = category if category else None
    news.author = user.username
    news.user_id = user_id
    storage.new(news)
    storage.save()

    return jsonify({"message": "News created successfully", "newsId": news.id}), 201


@app_views.route('/news/<news_id>', methods=['GET'], strict_slashes=False)
def get_news(news_id):
    """Retrieve a news article by ID"""
    news = storage.get(News, news_id)
    if not news:
        return jsonify({"error": "News not found"}), 404

    return jsonify({
        "news": {
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "publicationDate": str(news.created_at)
        }
    }), 200


@app_views.route('/news/<news_id>', methods=['PUT'], strict_slashes=False)
def update_news(news_id):
    """Update a news article by ID"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    news = storage.get(News, news_id)
    if not news:
        return jsonify({"error": "News not found"}), 404

    data = request.get_json()
    if data.get("title"):
        news.title = data["title"]
    if data.get("content"):
        news.content = data["content"]

    storage.save()
    return jsonify({"message": "News updated successfully"}), 200


@app_views.route('/news/<news_id>', methods=['DELETE'], strict_slashes=False)
def delete_news(news_id):
    """Delete a news article by ID"""
    if 'user_id' not in session:
        return jsonify({"error": "No active session"}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    news = storage.get(News, news_id)
    if not news:
        return jsonify({"error": "News not found"}), 404

    storage.delete(news)
    storage.save()
    return jsonify({"message": "News deleted successfully"}), 200


@app_views.route('/news', methods=['GET'], strict_slashes=False)
def list_news():
    """List all news articles"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    news = storage.all(News)

    # Pagination
    total_count = len(news)
    start_index = (page - 1) * limit
    end_index = page * limit
    news_articles = news[start_index:end_index]

    return jsonify({
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
    }), 200
