from fastapi import APIRouter, Request, Depends, Form, status, Response
from starlette.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas
from app.routers.users import get_current_user
from app.config import settings

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def ui_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/logout", response_class=HTMLResponse)
def ui_logout(request: Request):
    response = RedirectResponse(url="/ui", status_code=302)
    response.delete_cookie("access_token")
    return response

# Регистрация
@router.get("/register", response_class=HTMLResponse)
def ui_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
def ui_register_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user_data = schemas.UserCreate(username=username, password=password)
        user = crud.create_user(db, user_data)
        return templates.TemplateResponse("register_result.html", {"request": request, "message": f"Пользователь {user.username} успешно зарегистрирован. Теперь войдите."})
    except Exception as e:
        return templates.TemplateResponse("register_result.html", {"request": request, "error": str(e)})

# Вход – если уже вошёл, перенаправляем на главную
@router.get("/login", response_class=HTMLResponse)
def ui_login_form(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse(url="/ui", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
def ui_login_post(response: Response, request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        from app.routers.users import create_access_token
        user = crud.get_user_by_username(db, username=username)
        if not user:
            raise Exception("Неверное имя пользователя или пароль.")
        access_token = create_access_token(data={"sub": username})
        resp = templates.TemplateResponse("login_result.html", {"request": request, "message": f"Успешный вход. Ваш токен сохранён."})
        resp.set_cookie(key="access_token", value=access_token, httponly=True)
        return resp
    except Exception as e:
        return templates.TemplateResponse("login_result.html", {"request": request, "error": str(e)})

# Сокращение ссылки
@router.get("/shorten", response_class=HTMLResponse)
def ui_shorten_form(request: Request):
    return templates.TemplateResponse("shorten_form.html", {"request": request})

@router.post("/shorten", response_class=HTMLResponse)
def ui_shorten_post(
    request: Request,
    original_url: str = Form(...),
    custom_alias: str = Form(None),
    expires_at: str = Form(None),
    project: str = Form(None),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    owner_id = None
    if token:
        try:
            user = get_current_user(token, db)
            owner_id = user.id
        except Exception:
            pass
    link_create = schemas.LinkCreate(original_url=original_url, custom_alias=custom_alias, project=project)
    if expires_at:
        from datetime import datetime
        try:
            link_create.expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            return templates.TemplateResponse("shorten_result.html", {"request": request, "error": f"Неверный формат даты: {expires_at}"}, status_code=status.HTTP_400_BAD_REQUEST)
    try:
        db_link = crud.create_link(db, link_create, owner_id=owner_id)
        return templates.TemplateResponse("shorten_result.html", {
            "request": request,
            "base_url": settings.BASE_URL,
            "short_code": db_link.short_code,
            "original_url": db_link.original_url,
            "expires_at": db_link.expires_at,
            "project": db_link.project
        })
    except ValueError as ve:
        return templates.TemplateResponse("shorten_result.html", {"request": request, "error": str(ve)}, status_code=status.HTTP_400_BAD_REQUEST)

# Просмотр статистики
@router.get("/stats", response_class=HTMLResponse)
def ui_stats_form(request: Request):
    return templates.TemplateResponse("stats_form.html", {"request": request})

@router.get("/stats/result", response_class=HTMLResponse)
def ui_stats_result(request: Request, short_code: str, db: Session = Depends(get_db)):
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        return templates.TemplateResponse("stats_result.html", {"request": request, "error": f"Ссылка {short_code} не найдена."}, status_code=status.HTTP_404_NOT_FOUND)
    stats = schemas.LinkStats(
        original_url=db_link.original_url,
        created_at=db_link.created_at,
        last_accessed_at=db_link.last_accessed_at,
        redirect_count=db_link.redirect_count
    )
    return templates.TemplateResponse("stats_result.html", {"request": request, "stats": stats})

# Удаление ссылки – доступно только для зарегистрированных пользователей
@router.get("/delete", response_class=HTMLResponse)
def ui_delete_form(request: Request):
    return templates.TemplateResponse("delete_form.html", {"request": request, "info": "Введите short_code для удаления."})

@router.post("/delete", response_class=HTMLResponse)
def ui_delete_post(request: Request, short_code: str = Form(...), db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Эта функция доступна только для зарегистрированных пользователей. Пожалуйста, войдите."}, status_code=status.HTTP_401_UNAUTHORIZED)
    current_user = get_current_user(token, db)
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        return templates.TemplateResponse("delete_result.html", {"request": request, "error": f"Ссылка {short_code} не найдена."}, status_code=status.HTTP_404_NOT_FOUND)
    if db_link.owner_id != current_user.id:
        return templates.TemplateResponse("delete_result.html", {"request": request, "error": "Нет доступа для удаления этой ссылки."}, status_code=status.HTTP_403_FORBIDDEN)
    crud.record_expired_link(db, db_link)
    crud.delete_link(db, db_link)
    from app.caching import delete_cached_link
    delete_cached_link(short_code)
    return templates.TemplateResponse("delete_result.html", {"request": request, "message": f"Ссылка {short_code} успешно удалена."})

# Обновление ссылки – обновление происходит по вводу short_code; сервер перегенерирует короткую ссылку для того же оригинального URL
@router.get("/update", response_class=HTMLResponse)
def ui_update_form(request: Request):
    return templates.TemplateResponse("update_form.html", {"request": request, "info": "Введите short_code для обновления. После обновления старая ссылка будет удалена, и вы получите новую короткую ссылку с тем же оригинальным URL."})

@router.post("/update", response_class=HTMLResponse)
def ui_update_post(
    request: Request,
    short_code: str = Form(...),
    new_expires_at: str = Form(None),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if not token:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Эта функция доступна только для зарегистрированных пользователей. Пожалуйста, войдите."}, status_code=status.HTTP_401_UNAUTHORIZED)
    current_user = get_current_user(token, db)
    db_link = crud.get_link_by_code(db, short_code)
    if not db_link:
        return templates.TemplateResponse("update_result.html", {"request": request, "error": f"Ссылка {short_code} не найдена."}, status_code=status.HTTP_404_NOT_FOUND)
    if db_link.owner_id != current_user.id:
        return templates.TemplateResponse("update_result.html", {"request": request, "error": "Нет доступа для обновления этой ссылки."}, status_code=status.HTTP_403_FORBIDDEN)
    from app.schemas import LinkCreate
    new_link_data = LinkCreate(original_url=db_link.original_url, project=db_link.project)
    if new_expires_at:
        from datetime import datetime
        try:
            new_link_data.expires_at = datetime.fromisoformat(new_expires_at)
        except ValueError:
            return templates.TemplateResponse("update_result.html", {"request": request, "error": f"Неверный формат даты: {new_expires_at}"}, status_code=status.HTTP_400_BAD_REQUEST)
    new_db_link = crud.create_link(db, new_link_data, owner_id=current_user.id)
    crud.record_expired_link(db, db_link)
    crud.delete_link(db, db_link)
    from app.caching import delete_cached_link
    delete_cached_link(short_code)
    return templates.TemplateResponse("update_result.html", {"request": request, "short_code": new_db_link.short_code, "original_url": new_db_link.original_url, "expires_at": new_db_link.expires_at})

# Поиск по оригинальному URL
@router.get("/search", response_class=HTMLResponse)
def ui_search_form(request: Request):
    return templates.TemplateResponse("search_form.html", {"request": request})

@router.get("/search/result", response_class=HTMLResponse)
def ui_search_result(request: Request, original_url: str, db: Session = Depends(get_db)):
    db_link = crud.search_link_by_original(db, original_url)
    if not db_link:
        return templates.TemplateResponse("search_result.html", {"request": request, "error": f"Ссылка с оригинальным URL {original_url} не найдена."}, status_code=status.HTTP_404_NOT_FOUND)
    return templates.TemplateResponse("search_result.html", {"request": request, "short_code": db_link.short_code, "original_url": db_link.original_url, "created_at": db_link.created_at, "expires_at": db_link.expires_at})

# История удалённых ссылок для зарегистрированных пользователей
@router.get("/expired", response_class=HTMLResponse)
def ui_expired_links(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Эта функция доступна только для зарегистрированных пользователей. Пожалуйста, войдите."}, status_code=status.HTTP_401_UNAUTHORIZED)
    current_user = get_current_user(token, db)
    expired_links = crud.get_expired_links_by_user(db, current_user.id)
    return templates.TemplateResponse("expired_links.html", {"request": request, "expired_links": expired_links})

# Группировка ссылок по проектам для зарегистрированных пользователей
@router.get("/projects", response_class=HTMLResponse)
def ui_projects(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Эта функция доступна только для зарегистрированных пользователей. Пожалуйста, войдите."}, status_code=status.HTTP_401_UNAUTHORIZED)
    current_user = get_current_user(token, db)
    projects = crud.get_links_grouped_by_project(db, current_user.id)
    return templates.TemplateResponse("projects.html", {"request": request, "projects": projects})
