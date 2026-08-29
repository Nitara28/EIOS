from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import Organization, ActivityLog
from app.api.auth import get_current_organization

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs & Audit"])

@router.get("")
def list_activity_logs(org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    logs = db.query(ActivityLog).filter(
        ActivityLog.organization_id == org.id
    ).order_by(ActivityLog.created_at.desc()).limit(100).all()
    return logs
