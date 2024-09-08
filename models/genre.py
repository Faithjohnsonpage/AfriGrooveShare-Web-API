#!/usr/bin/env python3
"""
Genre class
"""
from sqlalchemy import Column, String
from models.base_model import BaseModel, Base
from typing import List, Dict, Any


class Genre(BaseModel, Base):
    """Representation of an Genre class"""
    __tablename__ = 'Genres'

    name = Column(String(255), nullable=False)

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes User"""
        super().__init__(*args, **kwargs)
