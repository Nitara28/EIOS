import os
import json
import re
import logging
import httpx
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.domain import DataSource, SyncJob, ActivityLog, Customer

load_dotenv()
logger = logging.getLogger("eios_whatsapp")

def normalize_phone_number(phone: Optional[str]) -> str:
    """
    Normalizes phone numbers by stripping all non-digit characters.
    e.g. "+91 98765-43210" -> "919876543210"
    """
    if not phone:
        return ""
    return re.sub(r'\D', '', phone)

class WhatsAppConnector:
    """
    Official WhatsApp Business Cloud API Connector.
    Handles configuration, webhook verification, inbound message ingestion,
    customer phone-number normalization & matching, outbound Graph API messaging,
    and audit logging.
    """

    @classmethod
    def get_env_credentials(cls) -> Dict[str, str]:
        return {
            "access_token": (os.getenv("WHATSAPP_ACCESS_TOKEN") or getattr(settings, "WHATSAPP_ACCESS_TOKEN", "") or "").strip(),
            "phone_number_id": (os.getenv("WHATSAPP_PHONE_NUMBER_ID") or getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") or "").strip(),
            "business_account_id": (os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID") or getattr(settings, "WHATSAPP_BUSINESS_ACCOUNT_ID", "") or "").strip(),
            "verify_token": (os.getenv("WHATSAPP_VERIFY_TOKEN") or getattr(settings, "WHATSAPP_VERIFY_TOKEN", "") or "").strip(),
            "api_version": (os.getenv("WHATSAPP_API_VERSION") or getattr(settings, "WHATSAPP_API_VERSION", "v18.0") or "v18.0").strip()
        }

    @classmethod
    def get_status(cls, organization_id: str, db: Session) -> Dict[str, Any]:
        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "WHATSAPP"
        ).first()

        env_creds = cls.get_env_credentials()
        has_token = bool((ds and ds.config and ds.config.get("access_token")) or env_creds["access_token"])
        has_phone_id = bool((ds and ds.config and ds.config.get("phone_number_id")) or env_creds["phone_number_id"])

        configured = has_token and has_phone_id
        phone_id = (ds.config.get("phone_number_id") if ds and ds.config else "") or env_creds["phone_number_id"]

        return {
            "configured": configured,
            "status": ds.status if ds else ("ACTIVE" if configured else "CONFIGURATION_READY"),
            "phone_number_id": phone_id if phone_id else None,
            "last_synced_at": ds.last_synced_at.isoformat() if ds and ds.last_synced_at else None
        }

    @classmethod
    def configure(cls, organization_id: str, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
        access_token = (payload.get("access_token") or "").strip()
        phone_number_id = (payload.get("phone_number_id") or "").strip()
        business_account_id = (payload.get("business_account_id") or "").strip()
        verify_token = (payload.get("verify_token") or "eios_whatsapp_verify_token").strip()

        if not access_token or not phone_number_id:
            return {
                "success": False,
                "error_code": "CREDENTIALS_REQUIRED",
                "message": "Both Access Token and Phone Number ID are required to configure WhatsApp Cloud API."
            }

        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "WHATSAPP"
        ).first()

        config_data = {
            "access_token": access_token,
            "phone_number_id": phone_number_id,
            "business_account_id": business_account_id,
            "verify_token": verify_token,
            "api_version": payload.get("api_version") or "v18.0"
        }

        if not ds:
            ds = DataSource(
                organization_id=organization_id,
                source_type="WHATSAPP",
                name="WhatsApp Business API",
                status="ACTIVE",
                last_synced_at=datetime.now(),
                config=config_data
            )
            db.add(ds)
        else:
            ds.status = "ACTIVE"
            ds.config = config_data
            ds.last_synced_at = datetime.now()

        # Audit Log (Never log access tokens)
        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name="Admin User",
            action="Configured WhatsApp Business Cloud API",
            source="WhatsApp Connector",
            status="SUCCESS",
            details=f"Configured WhatsApp Business API for Phone Number ID: {phone_number_id}",
            risk_level="MEDIUM"
        )
        db.add(log_entry)
        db.commit()

        return {
            "success": True,
            "status": "ACTIVE",
            "message": "WhatsApp Business Cloud API configured successfully."
        }

    @classmethod
    def disconnect(cls, organization_id: str, db: Session) -> Dict[str, Any]:
        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "WHATSAPP"
        ).first()

        if ds:
            ds.status = "DISCONNECTED"
            ds.config = None
            db.commit()

        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name="Admin User",
            action="Disconnected WhatsApp Business API",
            source="WhatsApp Connector",
            status="SUCCESS",
            details="Cleared WhatsApp Business API credentials and disconnected account.",
            risk_level="MEDIUM"
        )
        db.add(log_entry)
        db.commit()

        return {"success": True, "status": "DISCONNECTED", "message": "WhatsApp connection removed successfully."}

    @classmethod
    def verify_webhook(cls, mode: str, verify_token: str, challenge: str, organization_id: Optional[str], db: Session) -> Optional[int]:
        """
        Verifies Meta Webhook challenge request.
        """
        if mode != "subscribe":
            return None

        # Check configured verify_token in DB or env
        expected_token = ""
        if organization_id:
            ds = db.query(DataSource).filter(
                DataSource.organization_id == organization_id,
                DataSource.source_type == "WHATSAPP"
            ).first()
            if ds and ds.config:
                expected_token = ds.config.get("verify_token", "")

        if not expected_token:
            env_creds = cls.get_env_credentials()
            expected_token = env_creds["verify_token"] or "eios_whatsapp_verify_token"

        if verify_token == expected_token:
            try:
                return int(challenge)
            except ValueError:
                return challenge
        return None

    @classmethod
    def process_incoming_webhook(cls, payload: Dict[str, Any], organization_id: str, db: Session) -> Dict[str, Any]:
        """
        Processes inbound Meta WhatsApp webhook events.
        Matches sender phone numbers to Customer records in the specified organization.
        """
        entries = payload.get("entry", [])
        records_processed = 0
        records_imported = 0
        matched_customers = []

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                val = change.get("value", {})
                messages = val.get("messages", [])
                contacts = val.get("contacts", [])

                contact_name_map = {}
                for c in contacts:
                    wa_id = c.get("wa_id")
                    profile_name = c.get("profile", {}).get("name", "")
                    if wa_id:
                        contact_name_map[wa_id] = profile_name

                for msg in messages:
                    records_processed += 1
                    sender_phone = msg.get("from", "")
                    msg_id = msg.get("id", "")
                    msg_type = msg.get("type", "text")

                    body_text = ""
                    if msg_type == "text":
                        body_text = msg.get("text", {}).get("body", "")
                    else:
                        body_text = f"[{msg_type.upper()} media message]"

                    normalized_sender = normalize_phone_number(sender_phone)
                    sender_name = contact_name_map.get(sender_phone, f"+{sender_phone}")

                    # Search Customer records in organization
                    customer = None
                    org_customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
                    for cust in org_customers:
                        norm_cust_phone = normalize_phone_number(cust.phone)
                        if norm_cust_phone and (norm_cust_phone in normalized_sender or normalized_sender in norm_cust_phone):
                            customer = cust
                            break

                    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    if customer:
                        records_imported += 1
                        matched_customers.append(customer.name)
                        note_entry = f"\n[{timestamp_str} WhatsApp Inbound] Sender: {sender_name} (+{sender_phone}) | Message: '{body_text}'"
                        customer.notes = (customer.notes or "") + note_entry
                    else:
                        logger.info(f"WhatsApp inbound message from +{sender_phone} did not match existing customer in org {organization_id}.")

        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "WHATSAPP"
        ).first()

        if ds:
            ds.last_synced_at = datetime.now()

        sync_job = SyncJob(
            organization_id=organization_id,
            data_source_id=ds.id if ds else "ds-whatsapp",
            status="COMPLETED",
            records_processed=records_processed,
            records_imported=records_imported,
            summary=f"Processed {records_processed} WhatsApp messages. Matched {records_imported} customer phone profiles."
        )
        db.add(sync_job)

        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name="WhatsApp Webhook Worker",
            action="Processed Inbound WhatsApp Webhook",
            source="WhatsApp Connector",
            status="SUCCESS",
            details=f"Processed {records_processed} inbound messages. Matched customers: {', '.join(matched_customers) if matched_customers else 'None'}",
            risk_level="LOW"
        )
        db.add(log_entry)
        db.commit()

        return {
            "status": "SUCCESS",
            "records_processed": records_processed,
            "records_imported": records_imported,
            "matched_customers": matched_customers
        }

    @classmethod
    async def send_message(
        cls,
        organization_id: str,
        recipient_phone: str,
        message_body: str,
        db: Session,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an outbound WhatsApp message via Meta Graph API.
        Enforces that execution is only marked REAL & EXECUTED after Meta API confirms delivery.
        """
        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "WHATSAPP"
        ).first()

        env_creds = cls.get_env_credentials()
        access_token = (ds.config.get("access_token") if ds and ds.config else "") or env_creds["access_token"]
        phone_number_id = (ds.config.get("phone_number_id") if ds and ds.config else "") or env_creds["phone_number_id"]
        api_version = (ds.config.get("api_version") if ds and ds.config else "") or env_creds["api_version"] or "v18.0"

        if not access_token or not phone_number_id:
            return {
                "success": False,
                "error_code": "WHATSAPP_NOT_CONFIGURED",
                "execution_mode": "REAL",
                "external_confirmation": False,
                "message": "WhatsApp Business Cloud API is unconfigured. Access token and Phone Number ID are required."
            }

        clean_recipient = normalize_phone_number(recipient_phone)
        if not clean_recipient:
            return {
                "success": False,
                "error_code": "INVALID_PHONE_NUMBER",
                "message": "Recipient phone number is invalid."
            }

        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        if template_name:
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en_US"}
                }
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_recipient,
                "type": "text",
                "text": {"body": message_body}
            }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=10.0)

            if resp.status_code == 200:
                resp_json = resp.json()
                meta_msg_id = resp_json.get("messages", [{}])[0].get("id", "confirmed_meta_id")

                log_entry = ActivityLog(
                    organization_id=organization_id,
                    user_name="WhatsApp Dispatch Engine",
                    action=f"Sent WhatsApp Message to +{clean_recipient}",
                    source="WhatsApp Connector",
                    status="SUCCESS",
                    details=f"Meta Message ID: {meta_msg_id} | Phone: +{clean_recipient}",
                    risk_level="HIGH"
                )
                db.add(log_entry)
                db.commit()

                return {
                    "success": True,
                    "status": "EXECUTED",
                    "execution_mode": "REAL",
                    "external_confirmation": True,
                    "meta_message_id": meta_msg_id,
                    "message": f"WhatsApp message successfully delivered via Meta Graph API (ID: {meta_msg_id})."
                }
            else:
                error_body = resp.json().get("error", {})
                error_msg = error_body.get("message", resp.text)
                logger.error(f"Meta WhatsApp API Error [{resp.status_code}]: {error_msg}")

                log_entry = ActivityLog(
                    organization_id=organization_id,
                    user_name="WhatsApp Dispatch Engine",
                    action=f"Failed WhatsApp Dispatch to +{clean_recipient}",
                    source="WhatsApp Connector",
                    status="FAILED",
                    details=f"Meta API Error Code {resp.status_code}: {error_msg}",
                    risk_level="HIGH"
                )
                db.add(log_entry)
                db.commit()

                return {
                    "success": False,
                    "error_code": "WHATSAPP_API_ERROR",
                    "status_code": resp.status_code,
                    "execution_mode": "REAL",
                    "external_confirmation": False,
                    "message": f"Meta Graph API error: {error_msg}"
                }

        except Exception as e:
            logger.error(f"WhatsApp send HTTP exception: {e}")
            return {
                "success": False,
                "error_code": "WHATSAPP_API_ERROR",
                "execution_mode": "REAL",
                "external_confirmation": False,
                "message": f"HTTP dispatch failed: {str(e)}"
            }
