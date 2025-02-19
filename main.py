from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core import auth_router
from app.core.routes import router as pages_router

app = FastAPI(title="CareerDock")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates configuration
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(pages_router, tags=["pages"])
