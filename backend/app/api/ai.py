from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import Organization, User, AIConversation, AIMessage
from app.api.auth import get_current_organization, get_current_user
from app.schemas.schemas import AIQueryRequest, ActionCreate
from app.ai.ai_service import AIService
from app.actions.action_engine import ActionEngine

router = APIRouter(prefix="/ai", tags=["AI COO Engine"])

@router.post("/query")
def process_natural_language_query(
    req: AIQueryRequest,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Get or create conversation
    conversation_id = req.conversation_id
    if not conversation_id:
        conv = AIConversation(
            organization_id=org.id,
            user_id=user.id,
            title=req.query[:40] + ("..." if len(req.query) > 40 else "")
        )
        db.add(conv)
        db.flush()
        conversation_id = conv.id

    # Record User Message
    user_msg = AIMessage(
        conversation_id=conversation_id,
        sender="user",
        content=req.query
    )
    db.add(user_msg)

    # Process Query via AIService
    ai_result = AIService.process_query(
        query=req.query,
        organization_id=org.id,
        db=db
    )

    # Record Assistant Response
    assistant_msg = AIMessage(
        conversation_id=conversation_id,
        sender="assistant",
        content=ai_result["answer"],
        intent=ai_result["intent"],
        structured_data=ai_result["structured_data"],
        actions_created=ai_result["suggested_action"]
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "conversation_id": conversation_id,
        "answer": ai_result["answer"],
        "intent": ai_result["intent"],
        "filters_used": ai_result["filters_used"],
        "structured_data": ai_result["structured_data"],
        "suggested_action": ai_result["suggested_action"]
    }

@router.post("/action/submit")
def submit_ai_action(
    req: ActionCreate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    result = ActionEngine.submit_action(
        organization_id=org.id,
        action_type=req.action_type,
        payload=req.payload,
        created_by=f"AI Assistant ({user.full_name})",
        db=db
    )
    return result

@router.get("/conversations")
def list_conversations(user: User = Depends(get_current_user), org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    convs = db.query(AIConversation).filter(
        AIConversation.organization_id == org.id,
        AIConversation.user_id == user.id
    ).order_by(AIConversation.created_at.desc()).all()
    return convs
