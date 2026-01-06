import requests
import uuid
import json
import time

BASE_URL = "http://localhost:5001/api"
DEVICE_ID = str(uuid.uuid4())

def test_anonymous_flow():
    print(f"Testing with Device ID: {DEVICE_ID}")
    
    # Wait for server to be ready
    for i in range(5):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            break
        except Exception as e:
            print(f"Waiting for server... ({e})")
            time.sleep(1)
    
    # 1. Create Session
    print("\n1. Creating Session...")
    try:
        res = requests.post(f"{BASE_URL}/chat/sessions", json={
            "title": "Verification Test",
            "device_id": DEVICE_ID
        })
        if res.status_code != 200:
            print(f"FAILED: {res.text}")
            return
        session = res.json()
        session_id = session['id']
        print(f"SUCCESS: Session created {session_id}")
    except Exception as e:
        print(f"FAILED to connect: {e}")
        return

    # 2. Chat with specific query to test SQL execution
    print("\n2. Sending Message: 'Show me details for AE 328'")
    try:
        res = requests.post(f"{BASE_URL}/chat", json={
            "message": "Show me details for AE 328",
            "session_id": session_id,
            "device_id": DEVICE_ID
        })
        if res.status_code != 200:
            print(f"FAILED: {res.text}")
            return
        data = res.json()
        print(f"\nSUCCESS. Response:\n{data.get('response')}\n")
        
        if "SELECT" in data.get('response', '') and "{" in data.get('response', ''):
             print("❌ ERROR: Still returning raw SQL JSON!")
        else:
             print("✅ PASS: Returning natural language.")
             
    except Exception as e:
        print(f"FAILED: {e}")
        return

if __name__ == "__main__":
    test_anonymous_flow()
