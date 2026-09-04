"""
Nexus AI SDK Developer Demonstration
====================================
This script demonstrates how external applications and developers interact
with the Nexus AI platform using the official Python SDK.
"""

import sys
import os

# Ensure utf-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add parent directory to path so nexus_sdk can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nexus_sdk import NexusClient

def main():
    print("==================================================")
    print("🚀 Nexus AI Python SDK Demonstration")
    print("==================================================")

    # Initialize client with our master dev key
    client = NexusClient(
        api_key="nexus_dev_master_key",
        base_url="http://127.0.0.1:8000/v1"
    )

    # 1. Check available models
    print("\n[1] Listing Available Models...")
    try:
        models = client.models()
        for m in models:
            print(f"  • {m['id']}: {m['description']}")
    except Exception as e:
        print(f"  Error fetching models: {e}")

    # 2. Test Intent Classification Endpoint
    print("\n[2] Testing Intent Routing API...")
    try:
        classification = client.route.classify("Generate a futuristic cybernetic motorcycle in Tokyo")
        print(f"  Detected Intent: {classification['intent'].upper()}")
        print(f"  Target Prompt:   {classification['target_prompt']}")
    except Exception as e:
        print(f"  Error in route API: {e}")

    # 3. Test Standalone Web Search API
    print("\n[3] Testing Standalone Web Search API...")
    try:
        search_res = client.search.query("Artificial Intelligence latest news", max_results=2)
        print(f"  Found {search_res['count']} search results:")
        for r in search_res['results']:
            print(f"    - {r['title']} ({r['url'][:45]}...)")
    except Exception as e:
        print(f"  Error in search API: {e}")

    # 4. Test Standalone Image Generation API
    print("\n[4] Testing Image Generation API...")
    try:
        img_res = client.images.generate(prompt="A glowing quantum microprocessor chip, photorealistic")
        print(f"  Image URL: {img_res['data'][0]['url'][:65]}...")
        print(f"  Provider:  {img_res['provider']}")
    except Exception as e:
        print(f"  Error in image API: {e}")

    # 5. Test Multimodal Chat Streaming
    print("\n[5] Testing Multimodal Chat Streaming API...")
    try:
        print("  Streaming response from Nexus Omni:")
        stream = client.chat.create(
            messages=[{"role": "user", "content": "What is Nexus AI?"}],
            stream=True
        )
        for chunk in stream:
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"  Error in chat stream: {e}")

    # 6. Check Usage Metrics
    print("\n[6] Checking Platform Telemetry & Usage Metrics...")
    try:
        usage = client.usage()
        print(f"  Total Requests Logged: {usage['total_requests']}")
        print(f"  Active Endpoints:       {usage['requests_by_endpoint']}")
    except Exception as e:
        print(f"  Error fetching usage: {e}")

    print("\n==================================================")
    print("🎉 Nexus SDK Demo Completed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    main()
