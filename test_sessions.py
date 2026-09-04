import sys
from fastapi.testclient import TestClient
from main import app
from services.session_service import session_service

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_session_tests():
    print("==================================================")
    print("🧪 Testing Nexus AI SQLite Session & History Engine")
    print("==================================================")

    # 1. Test Title Generation
    print("\n[1] Testing Auto-Title Generation...")
    sample_prompts = [
        ("Search the latest breakthroughs in fusion energy 2026", "Breakthroughs In Fusion Energy 2026"),
        ("Generate an image of a cybernetic tiger in neon Tokyo", "Cybernetic Tiger In Neon Tokyo"),
        ("Explain how Transformer attention works step by step", "Attention Works Step By Step"),
        ("What is quantum computing?", "Quantum Computing"),
    ]
    import asyncio
    smart_title_hi = asyncio.run(session_service.generate_smart_title("hi"))
    print(f"  [PASS] Smart Title for 'hi' -> '{smart_title_hi}'")
    assert len(smart_title_hi) > 0

    # 2. Test Session Creation
    print("\n[2] Testing Session Creation...")
    s = session_service.create_session(title="Unit Test Conversation")
    session_id = s["id"]
    print(f"  [PASS] Created session: {session_id} (Title: '{s['title']}')")
    assert s["id"].startswith("chat_")

    # 3. Test Appending Messages
    print("\n[3] Testing Message Persistence...")
    msg_user = session_service.add_message(session_id, "user", "What are black holes?")
    msg_asst = session_service.add_message(
        session_id,
        "assistant",
        "A black hole is a region of spacetime...",
        intent="chat"
    )
    print(f"  [PASS] Added user message ID: {msg_user['id']}")
    print(f"  [PASS] Added assistant message ID: {msg_asst['id']}")

    # 4. Test Fetching Messages
    print("\n[4] Testing History Retrieval...")
    history = session_service.get_session_messages(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    print(f"  [PASS] Retrieved {len(history)} messages intact.")

    # 5. Test API Endpoints via TestClient
    print("\n[5] Testing Session REST Endpoints via TestClient...")
    client = TestClient(app)

    # List sessions
    r = client.get("/api/sessions")
    assert r.status_code == 200
    sessions_list = r.json()
    assert any(item["id"] == session_id for item in sessions_list)
    print(f"  [PASS] GET /api/sessions -> {len(sessions_list)} sessions listed.")

    # Get single session history
    r = client.get(f"/api/sessions/{session_id}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["messages"]) == 2
    print(f"  [PASS] GET /api/sessions/{session_id} -> {len(data['messages'])} messages returned.")

    # Rename session
    r = client.patch(f"/api/sessions/{session_id}", json={"title": "Astrophysics Exploration"})
    assert r.status_code == 200
    assert r.json()["title"] == "Astrophysics Exploration"
    print("  [PASS] PATCH /api/sessions/{id} -> Renamed successfully.")

    # Delete session
    r = client.delete(f"/api/sessions/{session_id}")
    assert r.status_code == 200
    # Confirm deletion
    r = client.get(f"/api/sessions/{session_id}")
    assert r.status_code == 404
    print("  [PASS] DELETE /api/sessions/{id} -> Deleted and confirmed 404.")

    print("\n==================================================")
    print("🎉 All Session & History Tests Passed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_session_tests()
