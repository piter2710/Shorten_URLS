from sqlalchemy import Integer, String, Column, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Shorten(Base):
    __tablename__ = "short_links"
    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String)
    short_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship('Users', back_populates='shorten')

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shorten = relationship('Shorten', back_populates='owner')

