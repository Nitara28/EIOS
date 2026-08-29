from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.domain import Organization, Task, Customer, Project
from app.api.auth import get_current_organization
from app.schemas.schemas import TaskCreate

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("")
def list_tasks(status: Optional[str] = None, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    query = db.query(Task).filter(Task.organization_id == org.id)
    if status:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.due_date.asc()).all()
    return tasks

@router.post("")
def create_task(req: TaskCreate, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    if req.customer_id:
        cust = db.query(Customer).filter(Customer.id == req.customer_id, Customer.organization_id == org.id).first()
        if not cust:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in organization.")

    if req.project_id:
        proj = db.query(Project).filter(Project.id == req.project_id, Project.organization_id == org.id).first()
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found in organization.")

    t = Task(
        organization_id=org.id,
        customer_id=req.customer_id,
        project_id=req.project_id,
        title=req.title,
        description=req.description,
        assigned_to=req.assigned_to,
        priority=req.priority,
        status=req.status,
        due_date=req.due_date
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t
