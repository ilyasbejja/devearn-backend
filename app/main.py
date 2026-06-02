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
import sqlite3
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

def apply_migrations():
    """Auto-migrate SQLite db if columns are missing"""
    import os
    db_path = "./devearn.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for missing columns in users table
            cursor.execute("PRAGMA table_info(users)")
            columns = [info[1] for info in cursor.fetchall()]
            
            def add_column_if_missing(col_name, col_type):
                if col_name not in columns:
                    print(f"[INFO] Adding missing column '{col_name}' to 'users' table...")
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

            add_column_if_missing("phone", "VARCHAR")
            add_column_if_missing("github_url", "VARCHAR")
            add_column_if_missing("linkedin_url", "VARCHAR")
            add_column_if_missing("website_url", "VARCHAR")
            add_column_if_missing("xp_points", "INTEGER DEFAULT 0")
            add_column_if_missing("specialty", "VARCHAR")
            
            # Email verification fields
            add_column_if_missing("is_verified", "BOOLEAN DEFAULT 0")
            add_column_if_missing("email_verification_code_hash", "VARCHAR")
            add_column_if_missing("email_verification_expires_at", "DATETIME")
            add_column_if_missing("email_verification_attempts", "INTEGER DEFAULT 0")
            add_column_if_missing("last_verification_sent_at", "DATETIME")

            # Password reset fields
            add_column_if_missing("password_reset_code_hash", "VARCHAR")
            add_column_if_missing("password_reset_expires_at", "DATETIME")
            add_column_if_missing("password_reset_attempts", "INTEGER DEFAULT 0")
            add_column_if_missing("last_reset_sent_at", "DATETIME")
            
            # Messages table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            tables = cursor.fetchone()
            if not tables:
                cursor.execute('''
                    CREATE TABLE messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER REFERENCES users(id),
                        receiver_id INTEGER REFERENCES users(id),
                        project_id INTEGER REFERENCES projects(id),
                        content VARCHAR,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                print("Created messages table.")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")

# Run migrations before creating tables to ensure new columns are added if DB exists
apply_migrations()
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