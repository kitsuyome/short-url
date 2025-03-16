import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    links = relationship("Link", back_populates="owner")

class Link(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(20), unique=True, index=True, nullable=False)
    custom_alias = Column(String(50), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    redirect_count = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project = Column(String(100), nullable=True)  # поле для указания проекта
    
    owner = relationship("User", back_populates="links")

class ExpiredLink(Base):
    __tablename__ = "expired_links"
    
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, nullable=False)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(20), nullable=False)
    owner_id = Column(Integer, nullable=True)
    project = Column(String(100), nullable=True)
    deleted_at = Column(DateTime, default=datetime.datetime.utcnow)
