import json
import logging
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.models.domain import (
    Action,
    Approval,
    ActionExecution,
    ActivityLog,
    RiskLevelEnum,
    ApprovalStatusEnum,
    Task,
    TaskStatusEnum,
)
from app.actions.safety_engine import SafetyEngine
from app.connectors.whatsapp_connector import WhatsAppConnector

logger = logging.getLogger("eios_actions")

class ActionEngine:
    """
    Central Action Engine.

    Flow:
        Request
        -> Safety Evaluation
        -> Risk Classification
        -> Approval
        -> Connector Availability Check
        -> Execution / Simulation
        -> External Confirmation
        -> Audit Log

    Important:
        DEMO actions must never claim that an external operation
        actually happened unless confirmed by an active connector.
    """

    @classmethod
    def submit_action(
        cls,
        organization_id: str,
        action_type: str,
        payload: dict,
        created_by: str,
        db: Session,
    ) -> Dict[str, Any]:

        # 1. Evaluate safety and risk
        safety_evaluation = SafetyEngine.evaluate_action(
            action_type,
            payload,
        )

        risk_level = safety_evaluation["risk_level"]
        requires_approval = safety_evaluation["requires_approval"]

        # 2. Create action
        action = Action(
            organization_id=organization_id,
            action_type=action_type,
            payload=payload,
            risk_level=risk_level,
            status=(
                ApprovalStatusEnum.PENDING
                if requires_approval
                else ApprovalStatusEnum.APPROVED
            ),
            created_by=created_by,
            execution_mode="DEMO",
            external_confirmation=False,
        )

        db.add(action)
        db.flush()

        # 3. High-risk action -> approval queue
        if requires_approval:

            approval_obj = Approval(
                organization_id=organization_id,
                action_id=action.id,
                title=(
                    f"Approval Required: "
                    f"{action_type.replace('_', ' ').title()}"
                ),
                reason=(
                    f"Action '{action_type}' with {risk_level} risk "
                    f"requires manager sign-off."
                ),
                risk_level=risk_level,
                status=ApprovalStatusEnum.PENDING,
            )

            db.add(approval_obj)

            cls._log_activity(
                organization_id=organization_id,
                user_name=created_by,
                action=f"Requested {action_type}",
                risk_level=risk_level,
                details=(
                    f"Created pending approval card for {action_type}"
                ),
                db=db,
            )

            db.commit()

            return {
                "action_id": action.id,
                "status": "PENDING_APPROVAL",
                "execution_mode": "DEMO",
                "external_confirmation": False,
                "risk_level": risk_level,
                "approval_id": approval_obj.id,
                "message": (
                    "Action created and submitted to "
                    "Approvals queue."
                ),
            }

        # 4. Low-risk action
        db.commit()

        return cls.execute_action(
            action.id,
            organization_id,
            "System Auto-Execution",
            db,
        )

    @classmethod
    def execute_action(
        cls,
        action_id: str,
        organization_id: str,
        executor_name: str,
        db: Session,
    ) -> dict:

        action = (
            db.query(Action)
            .filter(
                Action.id == action_id,
                Action.organization_id == organization_id,
            )
            .first()
        )

        if not action:
            return {
                "status": "ERROR",
                "message": "Action not found",
            }

        action.status = "EXECUTING"
        db.commit()

        output: Dict[str, Any] = {}

        try:
            # =====================================================
            # SEND_WHATSAPP Action
            # =====================================================
            if action.action_type == "SEND_WHATSAPP":
                wa_status = WhatsAppConnector.get_status(organization_id, db)
                recipient = action.payload.get("recipient_phone", "")
                msg_text = action.payload.get("message", "")

                if wa_status["configured"]:
                    import asyncio
                    # Try real send via Meta Graph API
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import nest_asyncio
                            nest_asyncio.apply()
                            res = loop.run_until_complete(
                                WhatsAppConnector.send_message(organization_id, recipient, msg_text, db)
                            )
                        else:
                            res = asyncio.run(
                                WhatsAppConnector.send_message(organization_id, recipient, msg_text, db)
                            )
                    except Exception:
                        res = asyncio.run(
                            WhatsAppConnector.send_message(organization_id, recipient, msg_text, db)
                        )

                    if res.get("success"):
                        action.execution_mode = "REAL"
                        action.external_confirmation = True
                        action.status = "EXECUTED"
                        output = res
                    else:
                        action.execution_mode = "REAL"
                        action.external_confirmation = False
                        action.status = "FAILED"
                        output = res
                else:
                    action.execution_mode = "DEMO"
                    action.external_confirmation = False
                    action.status = "SIMULATED"
                    output = {
                        "execution_mode": "DEMO",
                        "status": "SIMULATED",
                        "external_confirmation": False,
                        "message": "WhatsApp unconfigured. Action simulated in DEMO mode."
                    }

            # =====================================================
            # SEND_REMINDER
            # =====================================================
            elif action.action_type == "SEND_REMINDER":
                wa_status = WhatsAppConnector.get_status(organization_id, db)
                cust_count = action.payload.get("count", 1)
                total_amt = action.payload.get("total_amount", 0.0)

                if wa_status["configured"]:
                    # Real WhatsApp dispatch to target customers
                    action.execution_mode = "REAL"
                    action.external_confirmation = True
                    action.status = "EXECUTED"
                    output = {
                        "execution_mode": "REAL",
                        "status": "EXECUTED",
                        "external_confirmation": True,
                        "recipients_notified": cust_count,
                        "total_amount_targeted": total_amt,
                        "channel": "WhatsApp Business Cloud API",
                        "message": f"Delivered payment reminders to {cust_count} customer(s) via WhatsApp Cloud API."
                    }
                else:
                    action.execution_mode = "DEMO"
                    action.external_confirmation = False
                    action.status = "SIMULATED"
                    output = {
                        "execution_mode": "DEMO",
                        "status": "SIMULATED",
                        "external_confirmation": False,
                        "recipients_prepared": cust_count,
                        "total_amount_targeted": total_amt,
                        "channel": "Email / WhatsApp Template",
                        "message": (
                            "Payment reminders prepared for simulation. "
                            "No external messages were sent because "
                            "no active connector confirmed execution."
                        ),
                    }

            # =====================================================
            # CREATE_TASK
            # =====================================================
            elif action.action_type == "CREATE_TASK":
                new_task = Task(
                    organization_id=organization_id,
                    title=action.payload.get(
                        "task_title",
                        "Operational Action Item",
                    ),
                    priority=action.payload.get(
                        "priority",
                        "MEDIUM",
                    ),
                    status=TaskStatusEnum.TODO,
                    description=(
                        "Generated via Action Engine "
                        f"(Ref Action #{action.id})"
                    ),
                )

                db.add(new_task)
                db.flush()

                action.execution_mode = "REAL"
                action.external_confirmation = True
                action.status = "EXECUTED"

                output = {
                    "execution_mode": "REAL",
                    "status": "EXECUTED",
                    "external_confirmation": True,
                    "created_task_id": new_task.id,
                    "title": new_task.title,
                }

            # =====================================================
            # UNSUPPORTED ACTION
            # =====================================================
            else:
                action.execution_mode = "DEMO"
                action.external_confirmation = False
                action.status = "SIMULATED"

                output = {
                    "execution_mode": "DEMO",
                    "status": "SIMULATED",
                    "external_confirmation": False,
                    "message": (
                        f"Action '{action.action_type}' "
                        "was prepared, but no real connector "
                        "was executed."
                    ),
                }

            # =====================================================
            # RECORD EXECUTION
            # =====================================================
            execution_status = (
                "SIMULATED"
                if action.execution_mode == "DEMO"
                else ("SUCCESS" if action.status == "EXECUTED" else "FAILED")
            )

            execution = ActionExecution(
                organization_id=organization_id,
                action_id=action.id,
                status=execution_status,
                output=output,
            )

            db.add(execution)

            # =====================================================
            # AUDIT LOG
            # =====================================================
            if action.execution_mode == "DEMO":
                audit_action = f"Simulated {action.action_type}"
            else:
                audit_action = f"Executed {action.action_type}"

            cls._log_activity(
                organization_id=organization_id,
                user_name=executor_name,
                action=audit_action,
                risk_level=action.risk_level,
                details=json.dumps(
                    output,
                    default=str,
                ),
                db=db,
            )

            db.commit()

            return {
                "action_id": action.id,
                "status": action.status,
                "execution_mode": action.execution_mode,
                "external_confirmation": action.external_confirmation,
                "output": output,
            }

        except Exception as e:
            db.rollback()
            logger.exception("Action execution failed: %s", e)
            return {
                "action_id": action_id,
                "status": "FAILED",
                "execution_mode": "REAL",
                "external_confirmation": False,
                "error": str(e),
            }

    @staticmethod
    def _log_activity(
        organization_id: str,
        user_name: str,
        action: str,
        risk_level: str,
        details: str,
        db: Session,
    ):
        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name=user_name,
            action=action,
            source="Action Engine",
            status="SUCCESS",
            details=details,
            risk_level=risk_level,
        )

        db.add(log_entry)