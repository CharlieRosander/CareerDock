from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
from uuid import UUID
from typing import Optional
from fastapi import status

# Import routers and dependencies
from app.api.v1 import auth, users, job_ads
from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.security import decode_access_token
from app.services.user_service import get_user_by_id
from app.models.user import User

app = FastAPI(title="CareerDock")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Register API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(job_ads.router, prefix="/api/v1/job_ads", tags=["Job Ads"])


@app.middleware("http")
async def add_current_user_to_template(request: Request, call_next):
    response = await call_next(request)
    if hasattr(request.state, "user"):
        templates.env.globals["current_user"] = request.state.user
    else:
        templates.env.globals["current_user"] = None
    return response


@app.get("/api")
async def api_info():
    """
    API information
    """
    return {"message": "Welcome to CareerDock API"}


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Serve the login page with Jinja2 templates or redirect to dashboard if already logged in
    """
    # Check if user is already authenticated via cookie
    try:
        token = request.cookies.get("access_token")

        if token:
            try:
                user_id = decode_access_token(token)
                if user_id:
                    user = get_user_by_id(db, UUID(user_id))
                    if user:
                        # User is authenticated, redirect to dashboard
                        return RedirectResponse(url="/dashboard")
            except Exception:
                # Continue to login page on any error
                pass
    except Exception:
        # Continue to login page on any error
        pass

    # User is not authenticated, show login page
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Serve the dashboard page
    """
    # If user is not authenticated, redirect to login page
    if not current_user:
        return RedirectResponse(url="/")

    # User is authenticated, show dashboard
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "user_id": current_user.id,
            "user_name": current_user.full_name,
        },
    )


@app.get("/job-registry", response_class=HTMLResponse)
async def job_registry(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Serve the job registry page
    """
    return templates.TemplateResponse(
        "job_registry.html", {"request": request, "user": current_user}
    )
