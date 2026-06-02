from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.applications import router as applications_router
from app.routers.users import router as users_router
from app.routers.messages import router as messages_router
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(
    title="DevEarn Backend API",
    version="1.0.0"
)

# Ensure static/uploads exists
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://ilyasbejja.github.io",
    "null"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables in PostgreSQL (safe: only creates if they don't exist)
Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(projects_router, prefix="/projects", tags=["Projects"])
app.include_router(applications_router, prefix="/applications", tags=["Applications"])
app.include_router(messages_router, prefix="/messages", tags=["Messages"])


@app.get("/")
def root():
    return {
        "message": "DevEarn backend is running"
    }