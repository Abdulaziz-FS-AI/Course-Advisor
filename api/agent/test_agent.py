"""
Test script for KFUPM Course Advisor Agent.
Validates database connection, fuzzy search, and basic agent functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import get_agent, get_database, get_llm_client


def test_database_connection():
    """Test database connectivity and basic queries."""
    print("=" * 60)
    print("TEST: Database Connection")
    print("=" * 60)
    
    try:
        db = get_database()
        stats = db.get_table_stats()
        
        print("✅ Database connected successfully!")
        print("\nTable statistics:")
        for table, count in stats.items():
            print(f"  - {table}: {count:,} rows")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_fuzzy_search():
    """Test fuzzy search functionality."""
    print("\n" + "=" * 60)
    print("TEST: Fuzzy Search")
    print("=" * 60)
    
    try:
        db = get_database()
        
        # Test department search
        print("\nSearching departments for 'computer'...")
        dept_results = db.fuzzy_search_departments("computer", limit=3)
        if dept_results:
            print("✅ Found departments:")
            for r in dept_results:
                print(f"  - {r.get('name')} ({r.get('shortcut')})")
        else:
            print("⚠️ No department results (may need FTS5 setup)")
        
        # Test course search
        print("\nSearching courses for 'machine learning'...")
        course_results = db.fuzzy_search_courses("machine", limit=3)
        if course_results:
            print("✅ Found courses:")
            for r in course_results:
                print(f"  - {r.get('code')}: {r.get('title')}")
        else:
            print("⚠️ No course results")
        
        return True
    except Exception as e:
        print(f"❌ Fuzzy search failed: {e}")
        return False


def test_sql_execution():
    """Test direct SQL execution."""
    print("\n" + "=" * 60)
    print("TEST: SQL Execution")
    print("=" * 60)
    
    try:
        db = get_database()
        
        # Simple query
        sql = "SELECT code, title, credits FROM courses WHERE code LIKE 'ICS 1%' LIMIT 5"
        print(f"\nExecuting: {sql}")
        
        results, columns = db.execute_query(sql)
        
        if results:
            print(f"✅ Query returned {len(results)} rows")
            print(f"Columns: {columns}")
            for r in results[:3]:
                print(f"  - {r}")
        else:
            print("⚠️ No results returned")
        
        # Test dangerous SQL blocking
        print("\nTesting dangerous SQL blocking...")
        try:
            db.execute_query("DROP TABLE courses")
            print("❌ DANGER: DROP was not blocked!")
            return False
        except ValueError as e:
            print(f"✅ Dangerous SQL blocked correctly: {e}")
        
        return True
    except Exception as e:
        print(f"❌ SQL execution failed: {e}")
        return False


def test_llm_connection():
    """Test LLM server connectivity."""
    print("\n" + "=" * 60)
    print("TEST: LLM Connection")
    print("=" * 60)
    
    try:
        llm = get_llm_client()
        
        if llm.health_check():
            print(f"✅ LLM server connected at {llm.base_url}")
            return True
        else:
            print(f"⚠️ LLM server not responding at {llm.base_url}")
            print("   Make sure vLLM is running with the Qwen model")
            return False
    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        return False


def test_greeting_detection():
    """Test greeting classification."""
    print("\n" + "=" * 60)
    print("TEST: Greeting Detection")
    print("=" * 60)
    
    try:
        agent = get_agent()
        
        greetings = ["hi", "Hello!", "Hey there", "Good morning", "what's up"]
        non_greetings = ["What courses are in ICS?", "Tell me about SWE", "Show degree plan"]
        
        print("Testing greetings...")
        all_passed = True
        for g in greetings:
            is_greeting = agent._is_greeting(g)
            status = "✅" if is_greeting else "❌"
            print(f"  {status} '{g}' -> greeting={is_greeting}")
            if not is_greeting:
                all_passed = False
        
        print("\nTesting non-greetings...")
        for ng in non_greetings:
            is_greeting = agent._is_greeting(ng)
            status = "✅" if not is_greeting else "❌"
            print(f"  {status} '{ng}' -> greeting={is_greeting}")
            if is_greeting:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Greeting detection failed: {e}")
        return False


def test_agent_without_llm():
    """Test agent components that don't require LLM."""
    print("\n" + "=" * 60)
    print("TEST: Agent (without LLM)")
    print("=" * 60)
    
    try:
        agent = get_agent()
        
        # Test greeting response
        print("\nTesting greeting response...")
        result = agent._handle_greeting("hello")
        if "KFUPM Course Advisor" in result.message:
            print("✅ Greeting response generated correctly")
        else:
            print("❌ Greeting response missing expected content")
            return False
        
        # Test search term extraction
        print("\nTesting search term extraction...")
        terms = agent._extract_search_terms("What courses are in the ICS department about machine learning?")
        print(f"  Extracted terms: {terms}")
        if "ics" in [t.lower() for t in terms] or "ICS" in terms:
            print("✅ Search terms extracted correctly")
        else:
            print("⚠️ Expected 'ICS' in terms")
        
        return True
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and summarize results."""
    print("\n" + "=" * 60)
    print("KFUPM COURSE ADVISOR AGENT - TEST SUITE")
    print("=" * 60)
    
    results = {
        "Database Connection": test_database_connection(),
        "Fuzzy Search": test_fuzzy_search(),
        "SQL Execution": test_sql_execution(),
        "LLM Connection": test_llm_connection(),
        "Greeting Detection": test_greeting_detection(),
        "Agent (no LLM)": test_agent_without_llm(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    elif passed >= total - 1:
        print("\n⚠️ Most tests passed. LLM connection may need vLLM running.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()
