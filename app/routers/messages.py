from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List

from app.database import get_db
from app.models import Message, User, Project
from app.schemas import MessageCreate, MessageOut
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    msg: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify the project exists
    project = db.query(Project).filter(Project.id == msg.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    new_message = Message(
        sender_id=current_user.id,
        receiver_id=msg.receiver_id,
        project_id=msg.project_id,
        content=msg.content
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # To return sender_name
    msg_dict = {c.name: getattr(new_message, c.name) for c in new_message.__table__.columns}
    msg_dict["sender_name"] = current_user.full_name
    return msg_dict


@router.get("/threads")
def get_message_threads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active chat threads for the current user."""
    from sqlalchemy import or_
    messages = db.query(Message).filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()
    
    seen_threads = set()
    threads = []
    
    for msg in messages:
        other_user_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        thread_key = (msg.project_id, other_user_id)
        
        if thread_key in seen_threads:
            continue
        seen_threads.add(thread_key)
        
        other_user = db.query(User).filter(User.id == other_user_id).first()
        project = db.query(Project).filter(Project.id == msg.project_id).first()
        
        if not other_user or not project:
            continue
            
        threads.append({
            "project_id": msg.project_id,
            "project_title": project.title,
            "other_user_id": other_user.id,
            "other_user_name": other_user.full_name,
            "other_user_avatar": other_user.profile_picture,
            "last_message": msg.content,
            "last_message_time": msg.created_at.isoformat()
        })
        
    return threads


@router.get("/{project_id}/{other_user_id}", response_model=List[MessageOut])
def get_chat_history(
    project_id: int,
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = db.query(Message).filter(
        Message.project_id == project_id,
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    result = []
    for m in messages:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        m_dict = {c.name: getattr(m, c.name) for c in m.__table__.columns}
        m_dict["sender_name"] = sender.full_name if sender else "Inconnu"
        result.append(m_dict)

    return result
