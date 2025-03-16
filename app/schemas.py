from datetime import datetime
from typing import Optional
from pydantic import BaseModel, AnyUrl

class LinkBase(BaseModel):
    original_url: AnyUrl

class LinkCreate(LinkBase):
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None
    project: Optional[str] = None  # новый параметр

class LinkUpdate(BaseModel):
    # Обновление теперь применяется только к expires_at (обновление ссылки происходит путём перегенерации)
    expires_at: Optional[datetime] = None

class LinkStats(BaseModel):
    original_url: AnyUrl
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    redirect_count: int

class LinkOut(BaseModel):
    short_code: str
    original_url: AnyUrl
    created_at: datetime
    expires_at: Optional[datetime] = None
    project: Optional[str] = None

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
