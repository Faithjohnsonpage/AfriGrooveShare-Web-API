#!/usr/bin/env python3
from models.news import News
from datetime import datetime

# Create a new News instance
my_news = News()
my_news.title = "Breaking News"
my_news.content = "This is the content of the breaking news."
my_news.author = "John Doe"
my_news.published_at = datetime.utcnow()
my_news.category = "World"
my_news.user_id = "147da668-3a07-4a32-927a-5340b3e9d01c"

# Save the news to the database
my_news.save()

# Print the news object
print(my_news)
