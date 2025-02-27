from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

# Import routers and dependencies
from app.api.v1 import auth, users
from app.core.db import get_db
from app.core.auth import get_current_user

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
# app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
# app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    token: str = None,
    user_id: str = None,
    db: Session = Depends(get_db),
):
    """
    Serve the login page with Jinja2 templates
    """
    user = None
    if token:
        user = await get_current_user(db, token)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "token": token, "user_id": user_id, "user": user},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, token: str = None, db: Session = Depends(get_db)):
    """
    Serve the dashboard page
    """
    # First check if token is provided as query parameter
    if not token:
        # Then check cookies or authorization header
        token = request.cookies.get("access_token") or request.headers.get(
            "Authorization"
        )

        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

    user = await get_current_user(db, token)

    if not user:
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "user_id": user.id,
            "user_name": user.full_name,
        },
    )


@app.get("/auth/callback")
async def auth_callback(token: str = None, user_id: str = None):
    """
    Handle the callback from Google OAuth
    """
    if token and user_id:
        return RedirectResponse(url=f"/?token={token}&user_id={user_id}")
    return RedirectResponse(url="/")


@app.get("/api")
async def api_info():
    """
    API information
    """
    return {"message": "Welcome to CareerDock API"}
