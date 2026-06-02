from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Application, Project, User
from app.schemas import ApplicationCreate, ApplicationOut, ApplicationWithDetails
from app.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_to_project(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check project exists
    project = db.query(Project).filter(Project.id == application.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet introuvable"
        )

    # Check if already applied
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.project_id == application.project_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà postulé à ce projet"
        )

    new_app = Application(
        user_id=current_user.id,
        project_id=application.project_id,
        message=application.message,
    )

    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return new_app


@router.get("/me", response_model=List[ApplicationWithDetails])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all applications for the current student user, with project details."""
    applications = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.created_at.desc()).all()

    result = []
    for app in applications:
        project = db.query(Project).filter(Project.id == app.project_id).first()
        result.append(ApplicationWithDetails(
            id=app.id,
            user_id=app.user_id,
            project_id=app.project_id,
            message=app.message,
            status=app.status,
            created_at=app.created_at,
            project_title=project.title if project else "Projet supprimé",
            project_category=project.category if project else "",
            project_budget=project.budget if project else "",
        ))

    return result


@router.get("/project/{project_id}", response_model=List[ApplicationWithDetails])
def get_project_applications(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all applications for a specific project (owner only)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if project.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    applications = db.query(Application).filter(
        Application.project_id == project_id
    ).order_by(Application.created_at.desc()).all()

    result = []
    for app in applications:
        user = db.query(User).filter(User.id == app.user_id).first()
        result.append(ApplicationWithDetails(
            id=app.id,
            user_id=app.user_id,
            project_id=app.project_id,
            message=app.message,
            status=app.status,
            created_at=app.created_at,
            project_title=project.title,
            project_category=project.category,
            project_budget=project.budget,
            applicant_name=user.full_name if user else "Utilisateur inconnu",
            applicant_email=user.email if user else "",
        ))

    return result


@router.patch("/{application_id}/status")
def update_application_status(
    application_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept or reject an application (project owner only)."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    project = db.query(Project).filter(Project.id == application.project_id).first()
    if not project or project.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    if new_status not in ["Acceptée", "Refusée", "En attente"]:
        raise HTTPException(status_code=400, detail="Statut invalide")

    application.status = new_status
    db.commit()

    return {"message": f"Candidature mise à jour: {new_status}"}
