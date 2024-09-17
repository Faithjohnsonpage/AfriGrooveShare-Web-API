# AfriGrooveShare

AfriGrooveShare is a web API designed for sharing music. This API allows users to upload, manage, and stream their favorite tracks seamlessly. It provides robust functionality for user authentication, profile management, and music handling, making it a comprehensive solution for music sharing and interaction.

## Files

### `models/`

The `models/` directory contains the application's data models and database interaction logic. This directory includes:

- **`album.py`**: Defines the `Album` model, representing music albums in the system. It includes fields for album details and relationships with other models like `Artist` and `Genre`.
- **`artist.py`**: Defines the `Artist` model, which represents musical artists. This model includes fields for artist details and relationships with `Album` and `Music`.
- **`base_model.py`**: Contains the base model class with shared attributes and methods for other models. This includes common database fields and utility methods.
- **`genre.py`**: Defines the `Genre` model, which represents music genres. It includes fields for genre details and relationships with `Music` and `Album`.
- **`music.py`**: Defines the `Music` model, representing individual music tracks. This model includes fields for track details and relationships with `Album`, `Artist`, and `Genre`.
- **`news.py`**: Defines the `News` model, which represents news articles or updates related to the application. This model includes fields for article content and metadata.
- **`playlist.py`**: Defines the `Playlist` model, representing user-created playlists. It includes fields for playlist details and relationships with `Music` and `User`.
- **`user.py`**: Defines the `User` model, which represents users in the system.
- **`engine/`**: Contains database engine file:
  - **`db.py`**: Manages database connections and interactions. It includes setup for SQLAlchemy and other database configurations.

### `api/`

The `api/` directory contains the core implementation of the web API for the AfriGrooveShare application. It is structured as follows:

- **`__init__.py`**: Initializes the API module and sets up the API blueprint for version 1 of the application.

- **`v1/`**: Contains version 1 of the API, including the main application setup, views, and upload functionality:
  - **`__init__.py`**: Initializes the `v1` module and registers the API blueprint with the Flask application.
  - **`app.py`**: Configures and initializes the Flask application for version 1 of the API. This file includes application setup, registration of blueprints, and other configuration details.
  - **`uploads/`**: Contains directories and files for handling uploaded files, such as profile pictures and music files. This folder is used for storing and managing file uploads in the application.
  - **`views/`**: Contains the route handlers and view functions for the API endpoints:
    - **`__init__.py`**: Initializes the `views` module and sets up the route handlers for the API.
    - **`album.py`**: Defines routes and view functions related to album management, including creating, retrieving, updating, and deleting albums.
    - **`artist.py`**: Contains routes and view functions for managing artists, including CRUD operations and retrieving artist details.
    - **`genre.py`**: Provides routes and view functions for handling genres, including creating, updating, and retrieving genre information.
    - **`index.py`**: Defines the base routes for the API, typically including general information and health checks.
    - **`music.py`**: Contains routes and view functions related to music tracks, including uploading, retrieving, and managing music files.
    - **`news.py`**: Defines routes and view functions for handling news and updates within the application.
    - **`playlist.py`**: Provides routes and view functions for managing playlists, including adding and removing music tracks from playlists.
    - **`users.py`**: Contains routes and view functions for user management, including registration, login, profile updates, and password management.

### `tests/`

The `tests/` directory contains unit tests and integration tests for the AfriGrooveShare application. It is structured as follows:

- **`__init__.py`**: Initializes the `tests` module.

- **`models/`**: Contains tests for the application's models:
  - **`__init__.py`**: Initializes the `models` test module.
  - **`engine/`**: Includes tests specific to the database engine.
  - **`test_artist.py`**: Tests for the `Artist` model.
  - **`test_genre.py`**: Tests for the `Genre` model.
  - **`test_news.py`**: Tests for the `News` model.
  - **`test_user.py`**: Tests for the `User` model.
  - **`test_album.py`**: Tests for the `Album` model.
  - **`test_base_model.py`**: Tests for the base model functionality.
  - **`test_music.py`**: Tests for the `Music` model.
  - **`test_playlist.py`**: Tests for the `Playlist` model.

## Setup

```
$ pip3 install -r requirements.txt
```

Here's how you might write the `Run` section using the provided template:

---

## Run

To run the AfriGrooveShare Web API, you need to set the appropriate environment variables for the application and testing environments. Use the following commands to configure your environment and start the application:

### For Development

```bash
export AFRIGROOVE_USER=root
export AFRIGROOVE_PWD=your_password
export AFRIGROOVE_HOST=localhost
export AFRIGROOVE_DB=afrigroove
export SECRET_KEY=your_secret_key

API_HOST=0.0.0.0 API_PORT=5000 python3 -m api.v1.app
```

### For Testing

```bash
export AFRIGROOVE_USER=root
export AFRIGROOVE_PWD=your_password
export AFRIGROOVE_HOST=localhost
export AFRIGROOVE_DB=afrigroove_test
export SECRET_KEY=your_secret_key

export AFRIGROOVE_ENV=test

# Run tests using unittest
python3 -m unittest discover -s tests
```

Ensure that the database and necessary tables are set up before running the application or tests.

## Routes

### Index

- **`GET /api/v1/status`**: Returns the status of the API.
- **`GET /api/v1/stats`**: Returns the number of each object (users, artists, albums, music, playlists, news) in the database.

### Users

- **`POST /auth/register`**: Registers a new user. **Example:**
  ```bash
  curl -X POST localhost:5000/auth/register -d 'username=Bob Philip' -d 'email=bob@me.com' -d 'password=mySuperPwd'
  ```

- **`POST /auth/login`**: Authenticates a user and creates a session. **Example:**
  ```bash
  curl -X POST localhost:5000/auth/login -d 'email=bob@me.com' -d 'password=mySuperPwd'
  ```

- **`POST /auth/logout`**: Invalidates the user’s session. **Example:**
  ```bash
  curl -b "session=GfY3odG028fwAy63AbMeYh5906Hw4fFiu1uivSBeN6w.ePplscgQbWoNoobgKSY_pepgJYA" -X POST localhost:5000/auth/logout -v
  ```

- **`GET /users/me`**: Retrieves the authenticated user’s profile. **Example:**
  ```bash
  curl -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" -X GET localhost:5000/users/me -v
  ```

- **`PUT /users/me`**: Updates the authenticated user’s profile (username only). 

- **`POST /auth/reset-password`**: Requests a password reset by sending a token to the user’s email. 

- **`POST /auth/reset-password/confirm`**: Redirects to the change-password route using a reset token. 

- **`POST /auth/reset-password/change-password`**: Changes the user’s password after reset confirmation.

- **`POST /users/me/profile-picture`**: Updates the authenticated user’s profile picture. **Example:**
  ```bash
  curl -X POST http://localhost:5000/users/me/profile-picture -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" -F "file=@/home/ermac/AfriGrooveShare-Web-API/IMG_20230104_095203_922.jpg"
  ```

### Artists

- **`POST /artists`**: Creates a new artist. **Example:**
  ```bash
  curl -X POST http://localhost:5000/artists -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" -d "name=Psquare"
  ```

- **`GET /artists/<string:artist_id>`**: Retrieves an artist by ID. **Example:**
  ```bash
  curl -X GET http://localhost:5000/artists/bac8b0ef-5ea0-4767-bd4c-a5481b7f3db5 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA"
  ```

- **`PUT /artists/<string:artist_id>`**: Updates an artist by ID. **Example:**
  ```bash
  curl -X PUT http://localhost:5000/artists/bac8b0ef-5ea0-4767-bd4c-a5481b7f3db5 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" -d "bio=All round musician"
  ```

- **`DELETE /artists/<string:artist_id>`**: Deletes an artist by ID. **Example:**
  ```bash
  curl -X DELETE http://localhost:5000/artists/bac8b0ef-5ea0-4767-bd4c-a5481b7f3db5 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA"
  ```

- **`GET /artists`**: Lists all artists with pagination. **Example:**
  ```bash
  curl -X GET http://localhost:5000/artists
  ```

- **`POST /artists/<string:artist_id>/profile-picture`**: Updates the specified artist's profile picture. **Example:**
  ```bash
  curl -X POST http://localhost:5000/artists/fa1a3a4f-7a36-4105-b4aa-e3f1c026d346/profile-picture -F "file=@/home/ermac/AfriGrooveShare-Web-API/IMG_20230104_095203_922.jpg"
  ```

### Albums

- **`POST /albums`**: Creates a new album. **Example:**
  ```bash
  curl -X POST http://localhost:5000/albums?artist_id=375e26e0-42c1-4d61-898e-18ee55c20ed3 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" -d "title=Thriller" -d "release_date=1982-11-30"
  ```

- **`GET /albums/<string:album_id>`**: Retrieves an album by ID. **Example:**
  ```bash
  curl -X GET http://localhost:5000/albums/66b88f87-8f50-40fc-8fd1-389a87326917 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA"
  ```

- **`GET /albums`**: Lists all albums with pagination. **Example:**
  ```bash
  curl -X GET http://localhost:5000/albums -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA"
  ```

- **`POST /albums/<string:album_id>/cover-image`**: Updates the specified album's cover image. **Example:**
  ```bash
  curl -X POST http://localhost:5000/albums/66b88f87-8f50-40fc-8fd1-389a87326917/cover-image -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" -F "file=@/path/to/image.jpg"
  ```

### Genres

- **`GET /genres`**: Lists all predefined genres. **Example:**
  ```bash
  curl -X GET http://localhost:5000/genres
  ```

This endpoint retrieves a list of predefined genres, such as Pop, Rock, Jazz, Classical, Hip-Hop, Gospel, Electronic, Reggae, and Blues.


### Music

- **`POST /music/upload`**: Uploads a new music file. **Example:**
  ```bash
  curl -X POST http://127.0.0.1:5000/music/upload -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" \
  -F "title=My First Track" -F "description=This is a test track upload" -F "genre=Gospel" \
  -F "artist=Michael Jackson" -F "album=Greatest Hits" -F "duration=3:22" \
  -F "file=@/home/ermac/AfriGrooveShare-Web-API/- Lauren_Daigle_Power_To_Redeem_feat_All_Sons_Daughters_(mp3co.info).mp3"
  ```

- **`GET /music/<music_id>`**: Retrieves metadata for a specific music file by ID. **Example:**
  ```bash
  curl -X GET http://127.0.0.1:5000/music/e0c7c95f-1ac8-498e-b0e3-c2c2e97e3b8b
  ```

- **`GET /music`**: Lists all music files with optional filters. **Examples:**
  ```bash
  curl -X GET http://127.0.0.1:5000/music
  curl -X GET http://127.0.0.1:5000/music?genre=Rock
  curl -X GET "http://127.0.0.1:5000/music?album=Greatest%20Hits"
  curl -X GET "http://127.0.0.1:5000/music?genre=Rock&limit=2"
  ```

- **`POST /music/search`**: Searches for music based on a query string (searches titles, artists, albums, and genres). **Example:**
  ```bash
  curl -X POST http://127.0.0.1:5000/music/search -H "Content-Type: text/plain" -d "rock"
  ```

- **`GET /music/<music_id>/stream`**: Streams a specific music file by ID. **Example:**
  ```bash
  curl -X GET http://127.0.0.1:5000/music/e0c7c95f-1ac8-498e-b0e3-c2c2e97e3b8b/stream
  ```

### Playlist

- **`POST /playlist/create`**: Creates a new playlist. **Example:**
  ```bash
  curl -X POST http://127.0.0.1:5000/playlist/create -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" \
  -d "name=Living Legend" -d "description=Healing souls"
  ```

- **`POST /playlists/<playlist_id>`**: Updates a playlist by editing its metadata or adding/removing music. **Examples:**
  - Edit playlist description:
    ```bash
    curl -X POST http://127.0.0.1:5000/playlists/110acffc-850a-46eb-9e39-f9e551038fc7 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" \
    -d "action=edit" -d "description=The songs that lift souls"
    ```
  - Add music to playlist:
    ```bash
    curl -X POST http://127.0.0.1:5000/playlists/110acffc-850a-46eb-9e39-f9e551038fc7 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" \
    -d "action=add_music" -d "musicIds=e0c7c95f-1ac8-498e-b0e3-c2c2e97e3b8b" -d "musicIds=4c3bf4a5-ed88-42ae-aebd-36bdd60e8a29" -d "musicIds=981289ef-3f9d-490b-bc6b-7c2b3d6f996d"
    ```
  - Remove music from playlist:
    ```bash
    curl -X POST http://127.0.0.1:5000/playlists/110acffc-850a-46eb-9e39-f9e551038fc7 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA" \
    -d "action=remove_music" -d "musicIds=e0c7c95f-1ac8-498e-b0e3-c2c2e97e3b8b"
    ```

- **`DELETE /playlists/<playlist_id>`**: Deletes a playlist. **Example:**
  ```bash
  curl -X DELETE http://127.0.0.1:5000/playlists/110acffc-850a-46eb-9e39-f9e551038fc7 -b "session=oeOrbo0TD8j-KIzTiuQ3w4fpTbISglEyAK7u9MAoUjc.tn5U1nX3aEBsSlPwEUqylwOqKdA"
  ```

- **`GET /playlists/<playlist_id>`**: Retrieves metadata for a specific playlist by ID, including all associated music. **Example:**
  ```bash
  curl -X GET http://127.0.0.1:5000/playlists/068b2bad-ad39-495e-acdb-f5550484444b
  ```

### News

- **`POST /news`**: Creates a news article. **Example:**
  ```bash
  curl -X POST http://localhost:5000/news -b "session=Xe62m1bgXrZ1n9zeB67TsjsEcCHEloi2bnm3WB7Eq3E.VHCMGylo0yzvCnbAt1-9IAsqZUc" \
  -F "title=New Developments in Music Technology" -d "content=Exciting advancements in music technology..." -d "category=Music Technology"
  ```

- **`GET /news/<news_id>`**: Retrieves a news article by ID. **Example:**
  ```bash
  curl -X GET http://localhost:5000/news/f536e8d7-eee2-4371-aa98-e731b1a8b4ae
  ```

- **`PUT /news/<news_id>`**: Updates a news article by ID. **Example:**
  ```bash
  curl -X PUT http://localhost:5000/news/f536e8d7-eee2-4371-aa98-e731b1a8b4ae -b "session=Xe62m1bgXrZ1n9zeB67TsjsEcCHEloi2bnm3WB7Eq3E.VHCMGylo0yzvCnbAt1-9IAsqZUc" \
  -H "Content-Type: application/json" -d '{"title": "Updated Music Technology News", "content": "More exciting developments in music technology..."}'
  ```

- **`DELETE /news/<news_id>`**: Deletes a news article by ID. **Example:**
  ```bash
  curl -X DELETE http://localhost:5000/news/f536e8d7-eee2-4371-aa98-e731b1a8b4ae -b "session=Xe62m1bgXrZ1n9zeB67TsjsEcCHEloi2bnm3WB7Eq3E.VHCMGylo0yzvCnbAt1-9IAsqZUc"
  ```

- **`GET /news`**: Lists all news articles with pagination. **Examples:**
  ```bash
  curl -X GET http://localhost:5000/news
  curl -X GET "http://localhost:5000/news?page=2&limit=5"
  ```

## Conclusion

The AfriGrooveShare Web API provides a robust platform for managing music content, news articles, and user sessions. With its secure and flexible session management, user authentication, and various endpoints for interacting with music and news content, the API offers a comprehensive solution for music lovers, artists, and content creators.

### Key Features:
- **User Authentication & Session Management**: Secure login sessions with Flask-Session and seamless API interaction.
- **Music & News Management**: Create, update, retrieve, and delete music files and news articles through well-defined RESTful endpoints.
- **Extensible Categories**: Support for predefined genres and news categories, ensuring content is organized for easy access and discovery.
- **Search & Streaming**: Efficient search functionality for music and real-time streaming support.
- **Pagination & Filtering**: Flexible pagination and filtering options to manage large datasets for music and news content.

### Getting Started
To get started with the API, ensure your environment is set up correctly, and follow the examples provided for each route. The API supports multiple file types and allows for easy scaling with additional features.

### Future Improvements:
The AfriGrooveShare API is designed to evolve, with plans to introduce:
- Enhanced search capabilities with advanced filtering options.
- Support for additional media types and formats.
- Integration with third-party services for music recommendations, social sharing, and analytics.

Feel free to contribute or customize the API to fit your specific needs. Thank you for using AfriGrooveShare, and happy coding!
