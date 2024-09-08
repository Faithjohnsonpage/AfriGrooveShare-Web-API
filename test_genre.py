#!/usr/bin/python3
from models.genre import Genre

# Create a new Genre instance
my_genre = Genre()
my_genre.name = "Rock"

# Save the genre to the database
my_genre.save()

# Print the genre object
print(my_genre)

