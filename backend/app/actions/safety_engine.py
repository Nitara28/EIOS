from typing import Dict, Any
from app.models.domain import RiskLevelEnum

class SafetyEngine:
    """
    Validates actions against system security policies and assigns risk levels.
    Enforces that high-risk actions require human approval before execution.
    """

    ACTION_RISK_MAP = {
        "CREATE_TASK": RiskLevelEnum.LOW,
        "GENERATE_REPORT": RiskLevelEnum.LOW,
        "DRAFT_EMAIL": RiskLevelEnum.MEDIUM,
        "UPDATE_RECORD": RiskLevelEnum.MEDIUM,
        "SEND_REMINDER": RiskLevelEnum.HIGH,
        "CREATE_PO_DRAFT": RiskLevelEnum.HIGH,
        "EXECUTE_PAYMENT": RiskLevelEnum.CRITICAL
    }

    @classmethod
    def evaluate_action(cls, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        risk_level = cls.ACTION_RISK_MAP.get(action_type, RiskLevelEnum.HIGH)

        requires_approval = risk_level in [RiskLevelEnum.MEDIUM, RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]

        return {
            "action_type": action_type,
            "risk_level": risk_level,
            "requires_approval": requires_approval,
            "is_allowed": True
        }
