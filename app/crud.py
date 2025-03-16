import datetime
import random
import string
from sqlalchemy.orm import Session
from app import models, schemas
from app.config import settings
from app.utils import generate_short_code
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Пользователи
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Ссылки
def create_link(db: Session, link: schemas.LinkCreate, owner_id: int = None):
    if link.custom_alias:
        existing = db.query(models.Link).filter(models.Link.custom_alias == link.custom_alias).first()
        if existing:
            raise ValueError("custom_alias уже используется.")
        short_code = link.custom_alias
    else:
        short_code = generate_short_code(settings.LINK_CODE_LENGTH)
        while db.query(models.Link).filter(models.Link.short_code == short_code).first():
            short_code = generate_short_code(settings.LINK_CODE_LENGTH)
    
    db_link = models.Link(
        original_url=link.original_url,
        short_code=short_code,
        custom_alias=link.custom_alias,
        expires_at=link.expires_at,
        owner_id=owner_id,
        project=link.project
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_link_by_code(db: Session, code: str):
    return db.query(models.Link).filter(models.Link.short_code == code).first()

def update_link(db: Session, db_link: models.Link, link_update: schemas.LinkUpdate):
    if link_update.expires_at:
        db_link.expires_at = link_update.expires_at
    db.commit()
    db.refresh(db_link)
    return db_link

def delete_link(db: Session, db_link: models.Link):
    db.delete(db_link)
    db.commit()

def increment_redirect_count(db: Session, db_link: models.Link):
    db_link.redirect_count += 1
    db_link.last_accessed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_link)
    return db_link

def search_link_by_original(db: Session, original_url: str):
    return db.query(models.Link).filter(models.Link.original_url == original_url).first()

def record_expired_link(db: Session, db_link: models.Link):
    expired = models.ExpiredLink(
        link_id=db_link.id,
        original_url=db_link.original_url,
        short_code=db_link.short_code,
        owner_id=db_link.owner_id,
        project=db_link.project
    )
    db.add(expired)
    db.commit()

def delete_expired_links(db: Session):
    now = datetime.datetime.utcnow()
    expired_links = db.query(models.Link).filter(models.Link.expires_at != None, models.Link.expires_at < now).all()
    count = 0
    for link in expired_links:
        record_expired_link(db, link)
        db.delete(link)
        count += 1
    db.commit()
    return count

def delete_unused_links(db: Session, inactive_days: int):
    from datetime import timedelta
    cutoff = datetime.datetime.utcnow() - timedelta(days=inactive_days)
    unused_links = db.query(models.Link).filter(models.Link.last_accessed_at != None,
                                                  models.Link.last_accessed_at < cutoff).all()
    count = 0
    for link in unused_links:
        record_expired_link(db, link)
        db.delete(link)
        count += 1
    db.commit()
    return count

def get_expired_links_by_user(db: Session, owner_id: int):
    return db.query(models.ExpiredLink).filter(models.ExpiredLink.owner_id == owner_id).all()

def get_links_grouped_by_project(db: Session, owner_id: int):
    links = db.query(models.Link).filter(models.Link.owner_id == owner_id).all()
    projects = {}
    for link in links:
        proj = link.project if link.project else "Без проекта"
        projects.setdefault(proj, []).append(link)
    return projects
