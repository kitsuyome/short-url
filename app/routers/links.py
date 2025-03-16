from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app import schemas, crud
from app.database import get_db
from app.routers.users import get_current_user
from app.caching import delete_cached_link

router = APIRouter()

@router.post("/shorten", response_model=schemas.LinkOut, summary="Создание короткой ссылки")
def create_short_link(link: schemas.LinkCreate, db: Session = Depends(get_db), token: str = Header(None)):
    owner_id = None
    if token:
        user = get_current_user(token, db)
        if user:
            owner_id = user.id
    try:
        db_link = crud.create_link(db, link, owner_id=owner_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    return db_link

@router.get("/{short_code}", summary="Перенаправление по короткой ссылке")
def redirect_link(short_code: str, db: Session = Depends(get_db)):
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    if db_link.expires_at and db_link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Ссылка устарела.")
    db_link = crud.increment_redirect_count(db, db_link)
    return RedirectResponse(url=db_link.original_url)

@router.delete("/{short_code}", summary="Удаление ссылки")
def delete_short_link(short_code: str, db: Session = Depends(get_db), token: str = Header(...)):
    current_user = get_current_user(token, db)
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    if db_link.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа для удаления этой ссылки.")
    crud.record_expired_link(db, db_link)
    crud.delete_link(db, db_link)
    delete_cached_link(short_code)
    return {"detail": f"Ссылка {short_code} успешно удалена."}

@router.put("/{short_code}", response_model=schemas.LinkOut, summary="Обновление ссылки")
def update_short_link(short_code: str, link_update: schemas.LinkUpdate, db: Session = Depends(get_db), token: str = Header(...)):
    current_user = get_current_user(token, db)
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    if db_link.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа для обновления этой ссылки.")
    # Обновление: генерируется новая короткая ссылка для того же оригинального URL
    new_link_data = schemas.LinkCreate(
        original_url=db_link.original_url,
        expires_at=link_update.expires_at,
        custom_alias=db_link.custom_alias,
        project=db_link.project
    )
    new_db_link = crud.create_link(db, new_link_data, owner_id=current_user.id)
    crud.record_expired_link(db, db_link)
    crud.delete_link(db, db_link)
    delete_cached_link(short_code)
    return new_db_link

@router.get("/{short_code}/stats", response_model=schemas.LinkStats, summary="Статистика по ссылке")
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    stats = schemas.LinkStats(
        original_url=db_link.original_url,
        created_at=db_link.created_at,
        last_accessed_at=db_link.last_accessed_at,
        redirect_count=db_link.redirect_count
    )
    return stats

@router.get("/search", response_model=schemas.LinkOut, summary="Поиск ссылки по оригинальному URL")
def search_link(original_url: str, db: Session = Depends(get_db)):
    db_link = crud.search_link_by_original(db, original_url)
    if not db_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    return db_link

@router.get("/projects", summary="Группировка ссылок по проектам", response_model=dict)
def get_projects(db: Session = Depends(get_db), token: str = Header(...)):
    current_user = get_current_user(token, db)
    projects = crud.get_links_grouped_by_project(db, current_user.id)
    return projects
