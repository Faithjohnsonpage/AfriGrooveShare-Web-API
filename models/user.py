#!/usr/bin/env python3
"""
User class
"""
import bcrypt
from sqlalchemy import Column, String, Text
from models.base_model import BaseModel, Base
from typing import List, Dict, Any


class User(BaseModel, Base):
    """Representation of a User class"""

    __tablename__ = 'Users' 

    username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    profile_picture_url = Column(Text, nullable=True)
    reset_token = Column(String(60), nullable=True)

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes User"""
        super().__init__(*args, **kwargs)

    def __setattr__(self, name: str, value: Any) -> None:
        """Sets a password with bycrypt encryption"""
        if name == "password":
            if value:
                # Hash the password and set the password_hash attribute
                salt = bcrypt.gensalt()
                self.password_hash = bcrypt.hashpw(value.encode(), salt).decode()
        else:
            super().__setattr__(name, value)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

