#!/usr/bin/env python3
"""
The Admin class
"""
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, ForeignKey
from models.user import User
from typing import List, Dict, Any


class Admin(BaseModel, Base):
    """Model to represent an Admin user"""
    __tablename__ = 'admins'

    user_id = Column(String(60), ForeignKey('Users.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes Artist"""
        super().__init__(*args, **kwargs)
