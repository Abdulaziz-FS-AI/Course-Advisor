import sys
import os
sys.path.append("/home/shared_dir/vercel_app")

try:
    from api.agent.auth import verify_password, get_password_hash, create_access_token
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

hash_val = "$2b$12$JtwEzFlWQkbXbALgLnEMu.ELmHhbAwpcVFJjo/CcVwgimm1QIn.fa"
try:
    # Just testing if verify runs without crashing, invalid password is fine
    res = verify_password("wrongpassword", hash_val)
    print(f"Verify result (should be False): {res}")
except Exception as e:
    print(f"Verify failed: {e}")

try:
    token = create_access_token({"sub": "test"})
    print(f"Token created: {token[:10]}...")
except Exception as e:
    print(f"Token creation failed: {e}")
