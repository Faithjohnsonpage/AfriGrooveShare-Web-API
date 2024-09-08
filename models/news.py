#!/usr/bin/env python3
"""
News class
"""
from sqlalchemy import Column, String, Text, DateTime
from models.base_model import BaseModel, Base
from datetime import datetime
from typing import List, Dict, Any


class News(BaseModel, Base):
    """Representation of an News class"""
    __tablename__ = 'News'

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    category = Column(String(255), nullable=False)

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes News"""
        super().__init__(*args, **kwargs)
