#!/usr/bin/env python3
"""DB module
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models.base_model import BaseModel, Base
from os import getenv
from typing import Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session

class DB:
    """Interacts with the MySQL database"""

    def __init__(self) -> None:
        """Instantiate a DBStorage object"""
        AFRIGROOVE_USER = getenv('AFRIGROOVE_USER')
        AFRIGROOVE_PWD = getenv('AFRIGROOVE_PWD')
        AFRIGROOVE_HOST = getenv('AFRIGROOVE_HOST')
        AFRIGROOVE_DB = getenv('AFRIGROOVE_DB')
 
        self.__engine = create_engine('mysql+mysqldb://{}:{}@{}/{}'.
                                      format(AFRIGROOVE_USER,
                                             AFRIGROOVE_PWD,
                                             AFRIGROOVE_HOST,
                                             AFRIGROOVE_DB))

    def get_engine(self):
        """Return the SQLAlchemy engine"""
        return self.__engine

    def new(self, obj: Type[BaseModel]) -> None:
        """Add the object to the current database session"""
        self.__session.add(obj)

    def save(self) -> None:
        """Commit all changes of the current database session"""
        self.__session.commit()

    def delete(self, obj: Optional[BaseModel] = None) -> None:
        """Delete from the current database session obj if not None"""
        if obj is not None:
            self.__session.delete(obj)

    def reload(self) -> None:
        """Reloads data from the database"""
        Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def close(self) -> None:
        """Call remove() method on the private session attribute"""
        if self.__session:
            self.__session.remove()

    def get(self, cls: Type[BaseModel], id: str) -> Optional[BaseModel]:
        """Retrieve an object by its primary key"""
        return self.__session.query(cls).get(id)

    def all(self, cls: Type[BaseModel]) -> List[BaseModel]:
        """Retrieve all objects of a specific class"""
        return self.__session.query(cls).all()

    def filter_by(self,
                  cls: Type[BaseModel],
                  **kwargs: Any
                  ) -> List[BaseModel]:
        """Retrieve objects based on specific criteria"""
        return self.__session.query(cls).filter_by(**kwargs).first()

    def count(self, cls: Type[BaseModel]) -> int:
        """Count the number of objects in a specific class"""
        return self.__session.query(cls).count()

    def update(self, obj: BaseModel, **kwargs: Any) -> None:
        """Update a specific object"""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.save()

    def bulk_insert(self, objs: List[BaseModel]) -> None:
        """Insert multiple objects at once"""
        self.__session.bulk_save_objects(objs)
        self.save()

    def execute_raw_sql(self, query: str) -> List[Dict[str, Any]]:
        """Execute raw SQL queries"""
        result = self.__engine.execute(query)
        return [dict(row) for row in result.fetchall()]

    def rollback(self) -> None:
        """Rollback the current database session"""
        if self.__session:
            self.__session.rollback()

    def exists(self, cls: Type[BaseModel], **kwargs: Any) -> bool:
        """Check if an object with specific criteria exists"""
        return self.__session.query(cls).filter_by(**kwargs).first() \
                    is not None

    def get_or_create(self,
                      cls: Type[BaseModel],
                      defaults: Optional[Dict[str, Any]] = None,
                      **kwargs: Any
                      ) -> BaseModel:
        """Retrieve an object if it exists, otherwise create it"""
        instance = self.filter_by(cls, **kwargs).first()
        if instance:
            return instance
        else:
            params = {**kwargs, **(defaults or {})}
            instance = cls(**params)
            self.new(instance)
            self.save()
            return instance