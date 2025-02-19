from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router

# Create FastAPI app
app = FastAPI(
    title="CareerDock",
    description="A modern job application tracking system",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router - this will include all routes including frontend pages
app.include_router(api_router)
