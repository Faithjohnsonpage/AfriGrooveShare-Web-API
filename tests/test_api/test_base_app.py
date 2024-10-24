#!/usr/bin/env python3
import unittest
import os
from flask import Flask
from flask_testing import TestCase
from api.v1.views import app_views
from models import storage
from flask_caching import Cache
import redis
import logging


class BaseTestCase(TestCase):
    def create_app(self):
        """Create and configure the Flask application for testing"""
        app = Flask(__name__)
        app.register_blueprint(app_views)

        # Configuration settings for testing
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

        # SQLAlchemy setup
        app.config['SQLALCHEMY_DATABASE_URI'] = storage.get_engine().url
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Cache setup
        REDIS_URL = 'redis://localhost:6379/2'
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = REDIS_URL
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300

        # Initialize cache
        self.cache = Cache(app)

        app.cache = self.cache

        # Disable logging during tests
        logging.disable(logging.CRITICAL)

        return app
