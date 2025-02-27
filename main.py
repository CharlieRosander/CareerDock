from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Import routers
from app.api.v1 import auth, users

app = FastAPI(title="CareerDock2")

# Mount static files
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates setup
# templates = Jinja2Templates(directory="app/templates")

# Register API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
# app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])

@app.get("/")
async def root():
    return {"message": "Welcome to CareerDock2 API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
