from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import get_db
from .auth.routes import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Dashboard-sida som kräver inloggning"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": current_user}
    )

@router.get("/jobs")
async def job_registry(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Job registry page that requires login"""
    return templates.TemplateResponse(
        "job_registry.html",
        {"request": request, "user": current_user}
    )
