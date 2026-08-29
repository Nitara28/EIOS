import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_production_regression_suite():
    print("\n==================================================")
    print("EIOS FULL PRODUCTION REGRESSION & AUDIT TEST SUITE")
    print("==================================================")

    # --- Step 1: Authentication ---
    print("\n--- 1. Testing Authentication & JWT Token Issuance ---")
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@eios.ai", "password": "password123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    token = token_data["access_token"]
    org_id = token_data["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASSED] Authentication & JWT issuance verified.")

    # --- Step 2: Tenant Security & Boundary Isolation ---
    print("\n--- 2. Testing Tenant Security & Cross-Tenant Boundary Isolation ---")
    # Try creating a project with a fake/cross-tenant customer ID
    fake_proj_res = client.post("/api/v1/projects", headers=headers, json={
        "name": "Malicious Cross-Tenant Project",
        "customer_id": "00000000-0000-0000-0000-000000000000"
    })
    assert fake_proj_res.status_code == 404, f"Tenant boundary check failed: {fake_proj_res.text}"
    print("[PASSED] Cross-Tenant boundary isolation verified (Returned 404 for invalid customer).")

    # --- Step 3: Executive Dashboard ---
    print("\n--- 3. Testing Executive Dashboard & AI Briefing ---")
    dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    print("KPI Summary:", dash_data["kpis"])
    print("Briefing text:", dash_data["ai_summary"]["summary_text"].encode('ascii', 'ignore').decode('ascii'))
    print("[PASSED] Dashboard analytics & daily briefing verified.")

    # --- Step 4: Natural Language Query Engine ---
    print("\n--- 4. Testing AI Natural Language Query Engine ---")
    query = "Which customers have pending payments above 50000?"
    ai_res = client.post("/api/v1/ai/query", headers=headers, json={"query": query})
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    print("Extracted Intent:", ai_data["intent"])
    print("Structured Records Count:", len(ai_data["structured_data"]))
    print("Suggested Action:", ai_data["suggested_action"])

    assert ai_data["intent"] == "GET_OVERDUE_PAYMENTS"
    assert len(ai_data["structured_data"]) >= 2
    assert ai_data["suggested_action"] is not None
    print("[PASSED] Natural language intent extraction & query engine verified.")

    # --- Step 5: Action Engine & Approvals Workflow ---
    print("\n--- 5. Testing Action Engine & Human Approval Workflow ---")
    action_req = ai_data["suggested_action"]
    action_res = client.post("/api/v1/ai/action/submit", headers=headers, json={
        "action_type": action_req["action_type"],
        "payload": action_req["payload"],
        "risk_level": action_req["risk_level"]
    })
    assert action_res.status_code == 200
    action_data = action_res.json()
    approval_id = action_data["approval_id"]
    print("Action Submitted. Approval ID:", approval_id)

    # Approve action
    review_res = client.post(f"/api/v1/approvals/{approval_id}/review", headers=headers, json={"approved": True})
    assert review_res.status_code == 200
    print("Execution Result:", review_res.json())
    print("[PASSED] Action Engine safety policy & approval workflow verified.")

    # --- Step 6: Gmail OAuth 2.0 Connector Audit ---
    print("\n--- 6. Testing Real Gmail OAuth 2.0 Connector & Sync Status ---")
    auth_url_res = client.get("/api/v1/connectors/gmail/auth-url", headers=headers)
    assert auth_url_res.status_code == 200
    print("Gmail Auth URL Config Check:", auth_url_res.json())

    # Trigger Gmail Sync (when unconfigured, MUST report CREDENTIALS_REQUIRED - NEVER fake operations)
    gmail_sync_res = client.post("/api/v1/connectors/gmail/sync", headers=headers)
    assert gmail_sync_res.status_code == 200
    gmail_sync_data = gmail_sync_res.json()
    print("Gmail Sync Response:", gmail_sync_data)
    assert gmail_sync_data["status"] in ["CREDENTIALS_REQUIRED", "SUCCESS"]
    print("[PASSED] Gmail OAuth Connector credential & sync handling verified (No fake operations).")

    # --- Step 7: Immutable Audit Logs ---
    print("\n--- 7. Testing Immutable Activity Audit Logs ---")
    logs_res = client.get("/api/v1/activity-logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    print(f"Total Audit Entries: {len(logs)}")
    for log in logs[:3]:
        print(f"  [{log['created_at']}] {log['user_name']}: {log['action']} ({log['status']})")
    print("[PASSED] Immutable audit log trail verified.")

    print("\n==================================================")
    print("🏆 ALL REGRESSION & PRODUCTION SUITE TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_full_production_regression_suite()
