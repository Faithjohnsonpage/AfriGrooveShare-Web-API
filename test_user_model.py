#!/usr/bin/env python3
"""
Test script for the User class with password hashing
"""
from models.user import User
from models import storage  # Assuming storage is your database engine or session manager

def test_user():
    # Create a new User instance
    new_user = User()
    new_user.username = "Lillian Bassey"
    new_user.email = "lillianbassey@example.com"
    new_user.password = "realsecurepassword"  # This will be hashed

    # Save the user to the database
    new_user.save()

    
    # Print results
    print(f"User created: {new_user}")

if __name__ == "__main__":
    test_user()
