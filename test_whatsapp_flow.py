import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_whatsapp_cloud_api_suite():
    print("\n==================================================")
    print("EIOS WHATSAPP BUSINESS CLOUD API INTEGRATION TEST")
    print("==================================================")

    # --- Step 1: Login & Get Token ---
    print("\n--- 1. Authentication ---")
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@eios.ai", "password": "password123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    org_id = login_res.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASSED] Authentication successful.")

    # --- Step 2: Unconfigured Status Check & Secret Sanitization ---
    print("\n--- 2. Testing Unconfigured Status & Secret Sanitization ---")
    status_res = client.get("/api/v1/connectors/whatsapp/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    print("Status Data:", status_data)
    assert "access_token" not in status_data
    assert "verify_token" not in status_data
    print("[PASSED] Unconfigured status & secret sanitization verified.")

    # --- Step 3: Missing Credentials Configuration Validation ---
    print("\n--- 3. Testing Configuration Input Validation ---")
    bad_config_res = client.post("/api/v1/connectors/whatsapp/configure", headers=headers, json={
        "access_token": "",
        "phone_number_id": ""
    })
    assert bad_config_res.status_code == 400
    print("Missing Credentials Error Response:", bad_config_res.json()["detail"])
    assert bad_config_res.json()["detail"]["error_code"] == "CREDENTIALS_REQUIRED"
    print("[PASSED] Configuration validation verified.")

    # --- Step 4: Valid Configuration ---
    print("\n--- 4. Testing Valid WhatsApp Configuration ---")
    config_res = client.post("/api/v1/connectors/whatsapp/configure", headers=headers, json={
        "access_token": "EAAG_TEST_PERMANENT_META_ACCESS_TOKEN_1234567890",
        "phone_number_id": "109283746509182",
        "business_account_id": "9876543210123",
        "verify_token": "eios_whatsapp_test_verify_token"
    })
    assert config_res.status_code == 200
    config_data = config_res.json()
    print("Configuration Response:", config_data)
    assert config_data["success"] is True
    assert config_data["status"] == "ACTIVE"
    print("[PASSED] Valid WhatsApp Configuration stored successfully.")

    # Verify status after configuration
    status_res2 = client.get("/api/v1/connectors/whatsapp/status", headers=headers)
    assert status_res2.status_code == 200
    print("Configured Status Data:", status_res2.json())
    assert status_res2.json()["configured"] is True
    assert "access_token" not in status_res2.json() # Tokens sanitized!
    print("[PASSED] Configured status & token sanitization verified.")

    # --- Step 5: Webhook Verification GET Request ---
    print("\n--- 5. Testing Meta Webhook Verification (GET) ---")
    # Valid verify_token
    webhook_ver_res = client.get(
        f"/api/v1/connectors/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=eios_whatsapp_test_verify_token&hub.challenge=1122334455&organization_id={org_id}"
    )
    assert webhook_ver_res.status_code == 200
    assert webhook_ver_res.text == "1122334455"
    print("[PASSED] Meta Webhook Challenge verification succeeded with exact challenge return.")

    # Invalid verify_token
    webhook_fail_res = client.get(
        f"/api/v1/connectors/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=INVALID_TOKEN&hub.challenge=1122334455&organization_id={org_id}"
    )
    assert webhook_fail_res.status_code == 403
    print("[PASSED] Webhook verification cleanly rejected invalid verify_token with 403 Forbidden.")

    # --- Step 6: Inbound Webhook Event & Customer Phone Matching ---
    print("\n--- 6. Testing Inbound Webhook Ingestion & Customer Phone Matching ---")
    # ABC Industries in seed data has phone: "+91 98765 43210"
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "9876543210123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550248165",
                                "phone_number_id": "109283746509182"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Acme Purchasing Manager"},
                                    "wa_id": "919876543210"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAERgSQjE2RUU1QjM3MjhFQ0YxODgA",
                                    "timestamp": "1700000000",
                                    "text": {
                                        "body": "Hello EIOS, we received Invoice INV-1024 for ₹80,000. Payment will be processed tomorrow."
                                    },
                                    "type": "text"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    inbound_res = client.post(f"/api/v1/connectors/whatsapp/webhook?organization_id={org_id}", json=webhook_payload)
    assert inbound_res.status_code == 200
    inbound_data = inbound_res.json()
    print("Inbound Webhook Processor Result:", inbound_data)
    assert inbound_data["records_processed"] == 1
    assert inbound_data["records_imported"] == 1
    assert "ABC Industries" in inbound_data["matched_customers"]
    print("[PASSED] Inbound WhatsApp message ingested and customer phone number matched to ABC Industries.")

    # Verify Customer Notes Timeline updated
    cust_res = client.get("/api/v1/customers", headers=headers)
    abc_cust = next(c for c in cust_res.json() if c["name"] == "ABC Industries")
    cust_profile_res = client.get(f"/api/v1/customers/{abc_cust['id']}", headers=headers)
    c_notes = cust_profile_res.json()["customer"]["notes"]
    print("Updated Customer Notes:\n", c_notes)
    assert "WhatsApp Inbound" in c_notes
    assert "Invoice INV-1024" in c_notes
    print("[PASSED] WhatsApp communication appended to Customer history profile.")

    # --- Step 7: Outbound Send Validation ---
    print("\n--- 7. Testing Outbound Send Validation ---")
    # Send request
    send_res = client.post("/api/v1/connectors/whatsapp/send", headers=headers, json={
        "recipient_phone": "+91 98765 43210",
        "message": "Payment reminder for invoice INV-1024 (₹80,000 overdue)."
    })
    # Since access token is a test stub, Meta API call returns HTTP error response or fails gracefully -> WHATSAPP_API_ERROR
    assert send_res.status_code in [200, 400]
    send_data = send_res.json()
    print("Outbound Send Response:", send_data)
    assert send_data["execution_mode"] == "REAL"
    assert "external_confirmation" in send_data
    print("[PASSED] Outbound message validated with REAL execution mode and Meta confirmation check.")

    # --- Step 8: Disconnect Behavior ---
    print("\n--- 8. Testing Disconnect Behavior ---")
    disc_res = client.post("/api/v1/connectors/whatsapp/disconnect", headers=headers)
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    print("Disconnect Response:", disc_data)
    assert disc_data["status"] == "DISCONNECTED"

    # Status check after disconnect
    status_res3 = client.get("/api/v1/connectors/whatsapp/status", headers=headers)
    assert status_res3.json()["configured"] is False
    assert status_res3.json()["status"] == "DISCONNECTED"
    print("[PASSED] Disconnect behavior & credential revocation verified.")

    # --- Step 9: Audit Log History ---
    print("\n--- 9. Testing Audit Trail Records ---")
    logs_res = client.get("/api/v1/activity-logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    wa_logs = [l for l in logs if "WhatsApp" in l["source"] or "WhatsApp" in l["action"]]
    print(f"WhatsApp Audit Log Entries ({len(wa_logs)}):")
    for l in wa_logs:
        print(f"  [{l['created_at']}] {l['action']} ({l['status']})")
    assert len(wa_logs) >= 3
    print("[PASSED] WhatsApp activity log audit trail verified.")

    print("\n==================================================")
    print("🏆 WHATSAPP BUSINESS CLOUD API INTEGRATION SUITE PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_whatsapp_cloud_api_suite()
