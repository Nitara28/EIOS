from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from app.core.database import get_db
from app.models.domain import Organization, Approval, Action, ApprovalStatusEnum, ActivityLog, User
from app.api.auth import get_current_organization, get_current_user
from app.schemas.schemas import ApprovalReview
from app.actions.action_engine import ActionEngine

router = APIRouter(prefix="/approvals", tags=["Approvals"])

@router.get("")
def list_approvals(status: Optional[str] = None, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    query = db.query(Approval).filter(Approval.organization_id == org.id)
    if status:
        query = query.filter(Approval.status == status)

    approvals = query.order_by(Approval.created_at.desc()).all()
    results = []
    for app in approvals:
        action = db.query(Action).filter(Action.id == app.action_id).first()
        results.append({
            "id": app.id,
            "action_id": app.action_id,
            "title": app.title,
            "reason": app.reason,
            "risk_level": app.risk_level,
            "status": app.status,
            "action_type": action.action_type if action else "UNKNOWN",
            "payload": action.payload if action else {},
            "created_by": action.created_by if action else "AI Assistant",
            "created_at": app.created_at
        })
    return results

@router.post("/{approval_id}/review")
def review_approval(approval_id: str, req: ApprovalReview, user: User = Depends(get_current_user), org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    app = db.query(Approval).filter(Approval.id == approval_id, Approval.organization_id == org.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if app.status != ApprovalStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval request is already in status '{app.status}'.")

    now = datetime.now(timezone.utc)
    app.reviewed_by = user.full_name
    app.reviewed_at = now

    if req.approved:
        app.status = ApprovalStatusEnum.APPROVED
        db.commit()

        # Trigger execution via ActionEngine
        result = ActionEngine.execute_action(
            action_id=app.action_id,
            organization_id=org.id,
            executor_name=user.full_name,
            db=db
        )

        app.status = ApprovalStatusEnum.EXECUTED
        db.commit()

        return {
            "success": True,
            "status": "APPROVED_AND_EXECUTED",
            "execution_result": result
        }
    else:
        app.status = ApprovalStatusEnum.REJECTED
        action = db.query(Action).filter(Action.id == app.action_id).first()
        if action:
            action.status = ApprovalStatusEnum.REJECTED

        # Log rejection
        log = ActivityLog(
            organization_id=org.id,
            user_name=user.full_name,
            action=f"Rejected Approval #{app.id}",
            source="Approval Workflow",
            status="REJECTED",
            details=f"Reason / Comments: {req.comments or 'Action rejected by manager.'}",
            risk_level=app.risk_level
        )
        db.add(log)
        db.commit()

        return {
            "success": True,
            "status": "REJECTED"
        }
