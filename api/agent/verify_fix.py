
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.agent import get_agent

def verify_fix():
    print("Verifying 'ENGL 104' hallucination fix...")
    agent = get_agent()
    query = "engl 104"
    
    # Simulate SQL failure by calling fuzzy fallback directly
    results, sql_desc = agent._execute_with_fuzzy_fallback("SELECT * FROM courses WHERE code='ENGL 104'", query)
    
    print(f"\nQuery: '{query}'")
    print(f"Results found: {len(results)}")
    if results:
        print(f"First result: {results[0].get('name')}")
    
    print(f"SQL Description: {sql_desc}")
    
    if "WARNING" in sql_desc:
        print("\n✅ SUCCESS: Warning flag triggered correctly!")
    else:
        print("\n❌ FAILURE: Warning flag NOT found in description.")

if __name__ == "__main__":
    verify_fix()
