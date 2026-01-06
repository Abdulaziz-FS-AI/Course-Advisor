import requests
import sys

BASE_URL = "http://localhost:5000/api"

def run_test():
    print("Starting System Verification...")
    
    # 1. Register User
    print("\n1. Testing Registration...")
    username = "test_user_v1"
    password = "password123"
    
    try:
        res = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
        if res.status_code == 200:
            print("✅ Registration Successful")
        elif res.status_code == 400 and "already exists" in res.text:
            print("⚠️ User already exists (Expected on re-run)")
        else:
            print(f"❌ Registration Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Login User
    print("\n2. Testing Login...")
    token = ""
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            token = data["token"]
            print(f"✅ Login Successful. Token: {token[:10]}...")
            if data["role"] != "user":
                print(f"❌ Unexpected role: {data['role']}")
        else:
            print(f"❌ Login Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 3. Chat Interaction (With Persistence)
    print("\n3. Testing Chat Persistence...")
    try:
        # Send message
        chat_payload = {
            "message": "Hello, testing persistence",
            "token": token
        }
        res = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        if res.status_code == 200:
            data = res.json()
            session_id = data["session_id"]
            print(f"✅ Chat Response Received. Session ID: {session_id}")
            
            # Verify History
            res_hist = requests.get(f"{BASE_URL}/history?token={token}")
            if res_hist.status_code == 200:
                sessions = res_hist.json()["sessions"]
                if any(s['id'] == session_id for s in sessions):
                    print("✅ Session found in history")
                else:
                    print("❌ Session NOT found in history")
            else:
                print(f"❌ Failed to fetch history: {res_hist.status_code}")
        else:
            print(f"❌ Chat Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

    # 4. Admin Access
    print("\n4. Testing Admin Access...")
    admin_token = ""
    try:
        # Login Admin
        res = requests.post(f"{BASE_URL}/auth/login", json={"username": "Kfupmsdaia", "password": "aerospace"})
        if res.status_code == 200:
            admin_token = res.json()["token"]
            print("✅ Admin Login Successful")
        else:
            print(f"❌ Admin Login Failed: {res.status_code}")
            return

        # Fetch Users
        res_users = requests.get(f"{BASE_URL}/admin/users?token={admin_token}")
        if res_users.status_code == 200:
            users = res_users.json()["users"]
            print(f"✅ Fetched {len(users)} users.")
            test_user_record = next((u for u in users if u["username"] == username), None)
            if test_user_record:
                print(f"✅ Found test user in admin list. Messages: {test_user_record['message_count']}")
            else:
                print("❌ Test user not found in admin list")
        else:
            print(f"❌ Failed to fetch users: {res_users.status_code}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    run_test()
