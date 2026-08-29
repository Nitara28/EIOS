import os
import json
import logging
import httpx
from dotenv import load_dotenv
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.domain import DataSource, SyncJob, ActivityLog, Customer

load_dotenv()
logger = logging.getLogger("eios_gmail")

class GmailConnector:
    """
    Official Gmail API OAuth 2.0 Connector.
    Handles Google OAuth URL generation, token exchange, token refresh, email syncing,
    customer entity matching, database persistence, and audit logging.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URI = "https://oauth2.googleapis.com/token"
    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

    @classmethod
    def get_google_credentials(cls) -> tuple[str, str, str]:
        client_id = (os.getenv("GOOGLE_CLIENT_ID") or getattr(settings, "GOOGLE_CLIENT_ID", "") or "").strip()
        client_secret = (os.getenv("GOOGLE_CLIENT_SECRET") or getattr(settings, "GOOGLE_CLIENT_SECRET", "") or "").strip()
        redirect_uri = (os.getenv("GOOGLE_REDIRECT_URI") or getattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/connectors/gmail/callback")).strip()
        return client_id, client_secret, redirect_uri

    @classmethod
    def get_authorization_url(cls, organization_id: str) -> Dict[str, Any]:
        client_id, _, redirect_uri = cls.get_google_credentials()
        if not client_id:
            return {
                "configured": False,
                "error": "GOOGLE_CLIENT_ID is not configured in backend environment. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable Google OAuth."
            }

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(cls.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": organization_id
        }
        auth_url = f"{cls.AUTH_URI}?{urlencode(params)}"

        return {
            "configured": True,
            "authorization_url": auth_url
        }

    @classmethod
    async def exchange_code_for_tokens(cls, code: str, organization_id: str, db: Session) -> Dict[str, Any]:
        client_id, client_secret, redirect_uri = cls.get_google_credentials()
        if not client_id or not client_secret:
            raise ValueError("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing.")

        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(cls.TOKEN_URI, data=payload)
            if resp.status_code != 200:
                logger.error(f"Gmail token exchange failed: {resp.text}")
                raise ValueError(f"Failed to exchange OAuth code: {resp.text}")

            tokens = resp.json()

        # Update or create DataSource record
        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "GMAIL"
        ).first()

        token_config = {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "token_type": tokens.get("token_type", "Bearer"),
            "expires_at": (datetime.now() + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat()
        }

        if not ds:
            ds = DataSource(
                organization_id=organization_id,
                source_type="GMAIL",
                name="Gmail Business Communications",
                status="CONNECTED",
                last_synced_at=datetime.now(),
                config=token_config
            )
            db.add(ds)
        else:
            ds.status = "CONNECTED"
            ds.config = token_config
            ds.last_synced_at = datetime.now()

        # Audit Log (Never log sensitive tokens)
        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name="Admin User",
            action="Authorized Gmail OAuth 2.0 Integration",
            source="Gmail Connector",
            status="SUCCESS",
            details="Successfully obtained OAuth authorization for Google API.",
            risk_level="MEDIUM"
        )
        db.add(log_entry)
        db.commit()

        return {"status": "SUCCESS", "message": "Gmail account authorized successfully."}

    @classmethod
    async def sync_gmail_messages(cls, organization_id: str, db: Session) -> Dict[str, Any]:
        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "GMAIL"
        ).first()

        if not ds or not ds.config or not ds.config.get("access_token"):
            return {
                "status": "CREDENTIALS_REQUIRED",
                "configured": False,
                "summary": "Gmail connector is unconfigured. Please connect Google OAuth credentials in Data Sources."
            }

        access_token = ds.config.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}

        records_processed = 0
        records_imported = 0
        matched_customers = []

        try:
            async with httpx.AsyncClient() as client:
                # Fetch recent message list
                list_resp = await client.get(f"{cls.GMAIL_API_BASE}/messages?maxResults=10", headers=headers)
                if list_resp.status_code == 401:
                    # Token expired -> attempt refresh if refresh_token available
                    refresh_token = ds.config.get("refresh_token")
                    if refresh_token:
                        client_id, client_secret, _ = cls.get_google_credentials()
                        ref_resp = await client.post(cls.TOKEN_URI, data={
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "refresh_token": refresh_token,
                            "grant_type": "refresh_token"
                        })
                        if ref_resp.status_code == 200:
                            new_tokens = ref_resp.json()
                            access_token = new_tokens.get("access_token")
                            ds.config["access_token"] = access_token
                            db.commit()
                            headers = {"Authorization": f"Bearer {access_token}"}
                            list_resp = await client.get(f"{cls.GMAIL_API_BASE}/messages?maxResults=10", headers=headers)
                        else:
                            ds.status = "DISCONNECTED"
                            db.commit()
                            return {
                                "status": "CREDENTIALS_EXPIRED",
                                "summary": "Gmail authorization expired. Re-authentication required."
                            }
                    else:
                        ds.status = "DISCONNECTED"
                        db.commit()
                        return {
                            "status": "CREDENTIALS_EXPIRED",
                            "summary": "Gmail access token expired and no refresh token found."
                        }

                if list_resp.status_code != 200:
                    return {"status": "ERROR", "summary": f"Gmail API error: {list_resp.status_code}"}

                messages_data = list_resp.json().get("messages", [])
                for msg_meta in messages_data:
                    records_processed += 1
                    msg_id = msg_meta.get("id")
                    msg_detail_resp = await client.get(f"{cls.GMAIL_API_BASE}/messages/{msg_id}", headers=headers)
                    if msg_detail_resp.status_code == 200:
                        msg_obj = msg_detail_resp.json()
                        snippet = msg_obj.get("snippet", "")
                        payload_headers = msg_obj.get("payload", {}).get("headers", [])

                        sender_email = ""
                        subject = ""
                        for h in payload_headers:
                            if h.get("name", "").lower() == "from":
                                sender_email = h.get("value", "")
                            elif h.get("name", "").lower() == "subject":
                                subject = h.get("value", "")

                        # Entity resolution: check if sender email matches a Customer
                        customer = None
                        if sender_email:
                            for c in db.query(Customer).filter(Customer.organization_id == organization_id).all():
                                if c.email and c.email.lower() in sender_email.lower():
                                    customer = c
                                    break

                        if customer:
                            records_imported += 1
                            matched_customers.append(customer.name)
                            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                            note_entry = f"\n[{timestamp_str} Gmail Sync] Subject: '{subject}' | Snippet: {snippet[:100]}"
                            customer.notes = (customer.notes or "") + note_entry

                ds.last_synced_at = datetime.now()
                sync_job = SyncJob(
                    organization_id=organization_id,
                    data_source_id=ds.id,
                    status="COMPLETED",
                    records_processed=records_processed,
                    records_imported=records_imported,
                    summary=f"Processed {records_processed} Gmail messages. Matched {records_imported} customer emails."
                )
                db.add(sync_job)

                log_entry = ActivityLog(
                    organization_id=organization_id,
                    user_name="Gmail Worker Sync",
                    action="Synced Gmail Messages",
                    source="Gmail Connector",
                    status="SUCCESS",
                    details=f"Processed {records_processed} messages. Entity matches: {', '.join(matched_customers) if matched_customers else 'None'}",
                    risk_level="LOW"
                )
                db.add(log_entry)
                db.commit()

                return {
                    "status": "SUCCESS",
                    "configured": True,
                    "records_processed": records_processed,
                    "records_imported": records_imported,
                    "matched_customers": matched_customers,
                    "summary": f"Gmail sync complete. Matched {records_imported} messages to existing customer profiles."
                }

        except Exception as e:
            logger.error(f"Gmail sync exception: {e}")
            return {"status": "ERROR", "summary": str(e)}

    @classmethod
    def revoke_credentials(cls, organization_id: str, db: Session) -> Dict[str, Any]:
        ds = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "GMAIL"
        ).first()

        if ds:
            ds.status = "DISCONNECTED"
            ds.config = None
            db.commit()

        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name="Admin User",
            action="Revoked Gmail OAuth Credentials",
            source="Gmail Connector",
            status="SUCCESS",
            details="Cleared Gmail OAuth tokens and disconnected account.",
            risk_level="MEDIUM"
        )
        db.add(log_entry)
        db.commit()

        return {"status": "SUCCESS", "message": "Gmail account disconnected."}
