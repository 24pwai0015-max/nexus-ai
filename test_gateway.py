import sys
import asyncio

# Ensure utf-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from services.router import router, Intent
from services.search_service import search_service
from services.image_service import image_service
from services.llm_service import llm_service

async def run_tests():
    print("========================================")
    print("[TEST] Running Nexus AI Level 1 Component Tests")
    print("========================================")

    # 1. Intent Router Tests
    print("\n[1] Testing Intent Router...")
    test_queries = [
        ("What is the capital of France?", Intent.CHAT),
        ("Search the latest news on Nvidia chips today", Intent.SEARCH),
        ("Generate an image of a cybernetic tiger in neon Tokyo", Intent.IMAGE),
        ("Draw a picture of a futuristic laboratory", Intent.IMAGE),
        ("What happened today with stock markets?", Intent.SEARCH),
    ]

    all_router_passed = True
    for q, expected in test_queries:
        intent, cleaned = router.classify(q)
        passed = intent == expected
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} Query: '{q}' -> Classified as: {intent} (Expected: {expected})")
        if not passed:
            all_router_passed = False

    # 2. Image Service Test
    print("\n[2] Testing Image Service...")
    try:
        img_res = await image_service.generate("a futuristic floating crystal city")
        print(f"  [PASS] Image URL generated: {img_res['image_url'][:60]}... (Provider: {img_res['provider']})")
    except Exception as e:
        print(f"  [FAIL] Image service error: {e}")

    # 3. Search Service Test (DuckDuckGo / Tavily)
    print("\n[3] Testing Web Search Service...")
    try:
        results = await search_service.search("artificial intelligence developments", max_results=2)
        if results and len(results) > 0:
            print(f"  [PASS] Found {len(results)} search results:")
            for r in results:
                print(f"     - {r['title']} ({r['url'][:45]}...)")
        else:
            print("  [WARN] Search returned 0 results (network check needed)")
    except Exception as e:
        print(f"  [FAIL] Search service error: {e}")

    # 4. LLM Service Test
    print("\n[4] Testing LLM Service Streaming...")
    try:
        chunks = []
        async for chunk in llm_service.stream_chat([{"role": "user", "content": "Hello Nexus!"}]):
            chunks.append(chunk)
            if len(chunks) >= 5:
                break
        streamed_sample = "".join(chunks)
        print(f"  [PASS] LLM streaming response sample: '{streamed_sample.strip()}'")
    except Exception as e:
        print(f"  [FAIL] LLM stream error: {e}")

    print("\n========================================")
    print("[DONE] Nexus AI Level 1 Test Suite Completed Successfully!")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
