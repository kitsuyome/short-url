from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.routers import links, users, frontend
from app.database import engine, Base
from app.tasks import schedule_cleanup_task

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener Service",
    description="Сервис для сокращения URL с аналитикой и управлением",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(links.router, prefix="/links", tags=["links"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(frontend.router, prefix="/ui", tags=["UI"])

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root(request: Request):
    return frontend.ui_index(request)

@app.on_event("startup")
async def startup_event():
    schedule_cleanup_task()
