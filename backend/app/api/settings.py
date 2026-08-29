from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import Organization, User, OrganizationMember
from app.api.auth import get_current_organization, get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("")
def get_settings(user: User = Depends(get_current_user), org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).all()
    team_list = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            team_list.append({
                "user_id": u.id,
                "name": u.full_name,
                "email": u.email,
                "role": m.role
            })

    return {
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "industry": org.industry,
            "currency": org.currency
        },
        "team": team_list,
        "ai_settings": {
            "provider": "Google Gemini 1.5 Flash",
            "safety_strictness": "HIGH",
            "auto_approve_low_risk": True
        }
    }
