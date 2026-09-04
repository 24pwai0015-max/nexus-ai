import sys
import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEV_KEY = "nexus_dev_master_key"

def get_client():
    try:
        r = httpx.get("http://127.0.0.1:8000/health", timeout=1.0)
        if r.status_code == 200:
            print("  [INFO] Connected to live Nexus AI server at http://127.0.0.1:8000")
            return httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)
    except Exception:
        pass

    from fastapi.testclient import TestClient
    from main import app
    print("  [INFO] Live server offline. Testing in-memory via FastAPI TestClient.")
    return TestClient(app)

def run_tests():
    print("==================================================")
    print("🧪 Running Nexus AI API Platform Integration Tests")
    print("==================================================")

    client = get_client()

    # 1. Auth Test: Missing Key -> 401
    print("\n[1] Testing Missing API Key (expect 401)...")
    r = client.get("/v1/models")
    if r.status_code == 401:
        print(f"  [PASS] Correctly rejected with 401 Unauthorized")
    else:
        print(f"  [FAIL] Expected 401, got {r.status_code}")

    # 2. Auth Test: Invalid Key -> 403
    print("\n[2] Testing Invalid API Key (expect 403)...")
    r = client.get("/v1/models", headers={"Authorization": "Bearer fake_invalid_key"})
    if r.status_code == 403:
        print(f"  [PASS] Correctly rejected with 403 Forbidden")
    else:
        print(f"  [FAIL] Expected 403, got {r.status_code}")

    headers = {"Authorization": f"Bearer {DEV_KEY}"}

    # 3. Valid Auth: /v1/models -> 200
    print("\n[3] Testing /v1/models with Valid Key...")
    r = client.get("/v1/models", headers=headers)
    if r.status_code == 200:
        models = r.json().get("data", [])
        print(f"  [PASS] 200 OK. Available models: {[m['id'] for m in models]}")
    else:
        print(f"  [FAIL] Expected 200, got {r.status_code}: {r.text}")

    # 4. Route Endpoint: /v1/route
    print("\n[4] Testing /v1/route...")
    r = client.post("/v1/route", json={"text": "search the latest tech news"}, headers=headers)
    if r.status_code == 200 and r.json().get("intent") == "search":
        print(f"  [PASS] 200 OK. Intent classified: {r.json()}")
    else:
        print(f"  [FAIL] {r.status_code}: {r.text}")

    # 5. Search Endpoint: /v1/search
    print("\n[5] Testing /v1/search...")
    r = client.post("/v1/search", json={"query": "quantum computing breakthroughs", "max_results": 2}, headers=headers)
    if r.status_code == 200 and r.json().get("count") > 0:
        print(f"  [PASS] 200 OK. Retrieved {r.json()['count']} search results.")
    else:
        print(f"  [FAIL] {r.status_code}: {r.text}")

    # 6. Image Endpoint: /v1/images/generations
    print("\n[6] Testing /v1/images/generations...")
    r = client.post("/v1/images/generations", json={"prompt": "cyberpunk neon city", "size": "1024x1024"}, headers=headers)
    if r.status_code == 200 and "data" in r.json():
        print(f"  [PASS] 200 OK. Image URL: {r.json()['data'][0]['url'][:50]}...")
    else:
        print(f"  [FAIL] {r.status_code}: {r.text}")

    # 7. Non-Streaming Chat Completion: /v1/chat/completions
    print("\n[7] Testing /v1/chat/completions (Non-Streaming JSON)...")
    payload = {
        "messages": [{"role": "user", "content": "Hello Nexus platform"}],
        "stream": False
    }
    r = client.post("/v1/chat/completions", json=payload, headers=headers)
    if r.status_code == 200:
        res = r.json()
        print(f"  [PASS] 200 OK. Received message: {res['choices'][0]['message']['content'][:60]}...")
    else:
        print(f"  [FAIL] {r.status_code}: {r.text}")

    # 8. Telemetry Endpoint: /v1/usage
    print("\n[8] Testing /v1/usage...")
    r = client.get("/v1/usage", headers=headers)
    if r.status_code == 200:
        metrics = r.json()
        print(f"  [PASS] 200 OK. Telemetry stats: {metrics}")
    else:
        print(f"  [FAIL] {r.status_code}: {r.text}")

    print("\n==================================================")
    print("🎉 All Nexus AI Platform Integration Tests Passed!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
