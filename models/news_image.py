#!/usr/bin/env python3
"""
News class
"""
from sqlalchemy import Column, String, ForeignKey
from models.base_model import BaseModel, Base
from models.news import News
from typing import List, Dict, Any


class NewsImage(BaseModel, Base):
    """Representation of a NewsImage class"""
    __tablename__ = 'NewsImages'

    news_id = Column(String(60), ForeignKey('News.id', ondelete='CASCADE'), nullable=False)
    image_url = Column(String(255), nullable=False)

    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """Initializes NewsImage"""
        super().__init__(*args, **kwargs)
