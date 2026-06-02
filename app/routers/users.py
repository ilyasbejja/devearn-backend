from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
import uuid

from app.database import get_db
from app.models import User, Application
from app.schemas import UserOut, UserProfileUpdate, StudentStatsOut, PublicProfileOut
from app.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=list[UserOut])
def get_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all users, optionally filtered by role."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return current_user

@router.patch("/me", response_model=UserOut)
def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile text fields."""
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    if profile_data.company_name is not None:
        current_user.company_name = profile_data.company_name
    if profile_data.skills_tags is not None:
        current_user.skills_tags = profile_data.skills_tags
    if profile_data.cv_url is not None:
        current_user.cv_url = profile_data.cv_url
    if profile_data.education_level is not None:
        current_user.education_level = profile_data.education_level
    if profile_data.institution is not None:
        current_user.institution = profile_data.institution
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.github_url is not None:
        current_user.github_url = profile_data.github_url
    if profile_data.linkedin_url is not None:
        current_user.linkedin_url = profile_data.linkedin_url
    if profile_data.website_url is not None:
        current_user.website_url = profile_data.website_url
    if profile_data.specialty is not None:
        current_user.specialty = profile_data.specialty
        
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me/stats", response_model=StudentStatsOut)
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current student's stats."""
    applications = db.query(Application).filter(Application.user_id == current_user.id).all()
    total_apps = len(applications)
    accepted = sum(1 for app in applications if app.status == "Acceptée")
    
    return StudentStatsOut(
        total_applications=total_apps,
        accepted_missions=accepted,
        total_xp=current_user.xp_points
    )


@router.get("/{user_id}/public", response_model=PublicProfileOut)
def get_user_public_profile(user_id: int, db: Session = Depends(get_db)):
    """Get public information of a user for clients/mentors."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    # Fetch completed projects
    completed_apps = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status == "Acceptée"
    ).all()
    
    completed_projects = []
    if completed_apps:
        proj_ids = [app.project_id for app in completed_apps]
        from app.models import Project
        projects = db.query(Project).filter(
            Project.id.in_(proj_ids),
            Project.status == "Terminé"
        ).all()
        for p in projects:
            creator = db.query(User).filter(User.id == p.created_by_user_id).first()
            p_dict = {c.name: getattr(p, c.name) for c in p.__table__.columns}
            p_dict["creator_name"] = creator.full_name if creator else "Inconnu"
            completed_projects.append(p_dict)
            
    return PublicProfileOut(
        id=user.id,
        full_name=user.full_name,
        role=user.role,
        profile_picture=user.profile_picture,
        bio=user.bio,
        skills_tags=user.skills_tags,
        cv_url=user.cv_url,
        education_level=user.education_level,
        institution=user.institution,
        github_url=user.github_url,
        linkedin_url=user.linkedin_url,
        website_url=user.website_url,
        xp_points=user.xp_points,
        specialty=user.specialty,
        completed_projects=completed_projects
    )

@router.post("/me/avatar", response_model=UserOut)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a profile picture/logo."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image.")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Remove old avatar if exists
    if current_user.profile_picture:
        old_path = os.path.join("static", current_user.profile_picture.split("/static/")[-1])
        if os.path.exists(old_path) and not old_path.endswith("default.png"):
            try:
                os.remove(old_path)
            except:
                pass
                
    # Save URL (assuming backend runs on localhost for dev, but relative path is safer)
    # The frontend will prepend the API base URL if needed, or we just store relative path
    current_user.profile_picture = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(current_user)
    
    return current_user
