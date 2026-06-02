from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func

from app.database import Base

import os
from dotenv import load_dotenv
load_dotenv()
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")
    
    # Profile fields
    profile_picture = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    company_name = Column(String, nullable=True) # For clients/companies
    skills_tags = Column(String, nullable=True) # For students/laureates
    cv_url = Column(String, nullable=True)
    education_level = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    xp_points = Column(Integer, default=0)
    specialty = Column(String, nullable=True) # For laureates/students
    
    # Email Verification
    is_verified = Column(Boolean, default=False)
    email_verification_code_hash = Column(String, nullable=True)  # Hashed code for security
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    email_verification_attempts = Column(Integer, default=0)
    last_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password Reset
    password_reset_code_hash = Column(String, nullable=True)  # Hashed code for security
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_attempts = Column(Integer, default=0)
    last_reset_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    level = Column(String, default="all")
    budget = Column(String, nullable=False)
    description = Column(String, nullable=False)
    skills = Column(String, nullable=False)
    status = Column(String, default="En attente")
    created_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    message = Column(String, default="")
    status = Column(String, default="En attente")  # En attente, Acceptée, Refusée
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())