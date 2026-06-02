from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Project, User, Application
from app.schemas import ProjectCreate, ProjectOut, ProjectStats
from app.auth import get_current_user

router = APIRouter()


def _enrich_project_dict(project: Project, user: User | None, db: Session) -> dict:
    p_dict = {c.name: getattr(project, c.name) for c in project.__table__.columns}
    if user:
        p_dict["creator_name"] = user.company_name or user.full_name
        p_dict["creator_logo"] = user.profile_picture
    else:
        p_dict["creator_name"] = "Inconnu"
        p_dict["creator_logo"] = None
    p_dict["application_count"] = (
        db.query(Application).filter(Application.project_id == project.id).count()
    )
    return p_dict


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_project = Project(
        title=project.title,
        category=project.category,
        budget=project.budget,
        description=project.description,
        skills=project.skills,
        created_by_user_id=current_user.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.get("/", response_model=List[ProjectOut])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [
        _enrich_project_dict(
            p, db.query(User).filter(User.id == p.created_by_user_id).first(), db
        )
        for p in projects
    ]


@router.get("/open", response_model=List[ProjectOut])
def get_open_projects(db: Session = Depends(get_db)):
    """Fetch projects that are open or en attente for students to apply to."""
    projects = db.query(Project).filter(Project.status.in_(["Ouvert", "En attente"])).all()
    return [
        _enrich_project_dict(
            p, db.query(User).filter(User.id == p.created_by_user_id).first(), db
        )
        for p in projects
    ]


@router.get("/me", response_model=List[ProjectOut])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.created_by_user_id == current_user.id).all()
    return [_enrich_project_dict(p, current_user, db) for p in projects]


@router.get("/stats", response_model=ProjectStats)
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregated stats for the current user's dashboard."""
    projects = db.query(Project).filter(Project.created_by_user_id == current_user.id).all()

    total = len(projects)
    active = sum(1 for p in projects if p.status != "Terminé")
    completed = sum(1 for p in projects if p.status == "Terminé")

    total_budget = 0
    for p in projects:
        try:
            val = float(p.budget.replace(",", "").replace(" ", "").replace("MAD", "").replace("k", "000").strip())
            total_budget += val
        except (ValueError, AttributeError):
            pass

    project_ids = [p.id for p in projects]
    total_apps = 0
    if project_ids:
        total_apps = db.query(Application).filter(Application.project_id.in_(project_ids)).count()

    return ProjectStats(
        total_projects=total,
        active_projects=active,
        completed_projects=completed,
        total_budget=total_budget,
        total_applications=total_apps
    )


@router.patch("/{project_id}/status")
def update_project_status(
    project_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if project.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    if new_status not in ["En attente", "En cours", "Terminé"]:
        raise HTTPException(status_code=400, detail="Statut invalide")

    project.status = new_status
    db.commit()

    return {"message": f"Statut mis à jour: {new_status}"}


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
        
    user = db.query(User).filter(User.id == project.created_by_user_id).first()
    return _enrich_project_dict(project, user, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if project.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    db.delete(project)
    db.commit()

