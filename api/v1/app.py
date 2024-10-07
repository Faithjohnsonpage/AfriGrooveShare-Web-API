#!/usr/bin/python3
""" Flask Application """
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_session import Session
from models import storage
from flask_caching import Cache
from api.v1.views import app_views


app = Flask(__name__)

# Flask-Session configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = storage.get_engine().url
app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions'
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_KEY_PREFIX'] = 'session:'

# Configure cache (Using Redis as a caching backend)
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

cache = Cache(app)
app.cache = cache

# Initialize Flask-Session
Session(app)

# Register blueprint for routing
app.register_blueprint(app_views)


# Enable Cross-Origin Resource Sharing (CORS)
cors = CORS(app, resources={r"/api/v1/*": {"origins": "*"}})


# Define teardown context to close DB connections
@app.teardown_appcontext
def close_db(error: Exception = None) -> None:
    """ Close Storage at the end of the request """
    storage.close()


# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error: Exception) -> str:
    """ Handle 404 errors (Resource Not Found) """
    return jsonify({"error": "Not found"}), 404


# Error handler for 401 Unauthorized
@app.errorhandler(401)
def unauthorized(error: Exception) -> str:
    """ Handle 401 errors (Unauthorized access) """
    return jsonify({"error": "Unauthorized"}), 401


# Error handler for 403 Forbidden
@app.errorhandler(403)
def forbidden(error: Exception) -> str:
    """ Handle 403 errors (Forbidden access) """
    return jsonify({"error": "Forbidden"}), 403


# Run the Flask app
if __name__ == '__main__':
    host = os.getenv('API_HOST', '0.0.0.0')
    port = os.getenv('API_PORT', '5000')
    app.run(host=host, port=port)
