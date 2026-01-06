import sys
import os
sys.path.append("/home/shared_dir/vercel_app")

# Force debug mode
os.environ["DEBUG_MODE"] = "true"

try:
    from api.agent.agent import get_agent
    agent = get_agent()
    print("Agent initialized")
    
    response = agent.process_query("hi")
    print(f"Response Message: {response.message}")
    print(f"Response Error: {response.error}")
    
except Exception as e:
    print(f"Test failed: {e}")
