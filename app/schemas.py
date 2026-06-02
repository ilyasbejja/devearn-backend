from pydantic import BaseModel, EmailStr
from datetime import datetime

import os
from dotenv import load_dotenv
load_dotenv()
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "student"


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class VerifyEmail(BaseModel):
    email: EmailStr
    code: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationCodeRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str
    confirm_password: str


class VerificationResponse(BaseModel):
    message: str
    success: bool


class ForgotPasswordResponse(BaseModel):
    message: str
    success: bool


class ResetPasswordResponse(BaseModel):
    message: str
    success: bool


class UserProfileUpdate(BaseModel):
    bio: str | None = None
    company_name: str | None = None
    skills_tags: str | None = None
    cv_url: str | None = None
    education_level: str | None = None
    institution: str | None = None
    phone: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    website_url: str | None = None
    specialty: str | None = None


class UserOut(UserBase):
    id: int
    profile_picture: str | None = None
    bio: str | None = None
    company_name: str | None = None
    skills_tags: str | None = None
    cv_url: str | None = None
    education_level: str | None = None
    institution: str | None = None
    phone: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    website_url: str | None = None
    xp_points: int = 0
    specialty: str | None = None
    is_verified: bool = False
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str | None = None


class TokenData(BaseModel):
    email: str | None = None


class ProjectBase(BaseModel):
    title: str
    category: str
    budget: str
    description: str
    skills: str


class ProjectCreate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    id: int
    level: str
    status: str
    created_by_user_id: int
    creator_name: str | None = None
    creator_logo: str | None = None
    created_at: datetime
    application_count: int = 0

    model_config = {
        "from_attributes": True
    }


class ApplicationCreate(BaseModel):
    project_id: int
    message: str = ""


class ApplicationOut(BaseModel):
    id: int
    user_id: int
    project_id: int
    message: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ApplicationWithDetails(ApplicationOut):
    project_title: str = ""
    project_category: str = ""
    project_budget: str = ""
    project_creator_id: int | None = None
    project_creator_name: str | None = None
    applicant_name: str = ""
    applicant_email: str = ""


class ProjectStats(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    total_budget: float = 0
    total_applications: int = 0


class StudentStatsOut(BaseModel):
    total_applications: int = 0
    accepted_missions: int = 0
    total_xp: int = 0


class PublicProfileOut(BaseModel):
    id: int
    full_name: str
    role: str
    profile_picture: str | None = None
    bio: str | None = None
    skills_tags: str | None = None
    cv_url: str | None = None
    education_level: str | None = None
    institution: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    website_url: str | None = None
    xp_points: int = 0
    specialty: str | None = None
    completed_projects: list[ProjectOut] = []


class MessageCreate(BaseModel):
    receiver_id: int
    project_id: int
    content: str


class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    project_id: int
    content: str
    created_at: datetime
    sender_name: str | None = None

    model_config = {
        "from_attributes": True
    }