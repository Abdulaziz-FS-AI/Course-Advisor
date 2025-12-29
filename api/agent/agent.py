"""
Main Agent Orchestrator for KFUPM Course Advisor.
Handles the complete flow: Query -> Classification -> SQL -> Execution -> Response
"""

import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .config import MAX_SQL_RETRIES, DEBUG_MODE
from .database import get_database, DatabaseManager
from .llm_client import get_llm_client, LLMClient
from .system_prompt import get_system_prompt, get_result_formatting_prompt


class QueryType(Enum):
    """Classification of user queries."""
    GREETING = "greeting"
    DATABASE_QUESTION = "database_question"
    CLARIFICATION = "clarification"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class AgentResponse:
    """Structured response from the agent."""
    message: str
    query_type: QueryType
    sql_used: Optional[str] = None
    raw_results: Optional[List[Dict]] = None
    error: Optional[str] = None


class CourseAdvisorAgent:
    """Main agent for handling course advising queries."""
    
    # Greeting patterns for quick classification
    GREETING_PATTERNS = [
        r'^(hi|hello|hey|greetings|good\s*(morning|afternoon|evening)|howdy|sup)[\s\!\?\.\,]*$',
        r'^(hi|hello|hey)[\s\!\?\.]*there[\s\!\?\.]*$',
        r'^what\'?s\s*up[\s\!\?\.]*$',
        r'^how\s*are\s*you[\s\!\?\.]*$',
    ]
    
    def __init__(self):
        self.db: DatabaseManager = get_database()
        self.llm: LLMClient = get_llm_client()
        self.system_prompt = get_system_prompt()
        self.conversation_history: List[Dict] = []
    
    def _is_greeting(self, query: str) -> bool:
        """Quick check if query is a simple greeting."""
        query_lower = query.lower().strip()
        for pattern in self.GREETING_PATTERNS:
            if re.match(pattern, query_lower, re.IGNORECASE):
                return True
        return False
    
    def _extract_sql(self, llm_response: str) -> Optional[str]:
        """Extract SQL query from LLM response."""
        # Try to find JSON block with SQL
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if data.get("type") == "sql_query" and "sql" in data:
                    return data["sql"].strip()
            except json.JSONDecodeError:
                pass
        
        # Try to find SQL in code block
        sql_match = re.search(r'```sql\s*(.*?)\s*```', llm_response, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        # Try to find raw SELECT statement
        select_match = re.search(r'(SELECT\s+.*?;)', llm_response, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()
        
        return None
    
    def _handle_greeting(self, query: str) -> AgentResponse:
        """Handle greeting queries with a friendly response."""
        greeting_response = """👋 Hello! I'm your **KFUPM Course Advisor**. I can help you find information about:

📚 **Courses** - Details, prerequisites, credits, and descriptions
🏛️ **Departments** - All colleges and their programs
📋 **Degree Plans** - Course sequences for each major
🎯 **Concentrations** - Specialization tracks available

What would you like to know about KFUPM academics?"""
        
        return AgentResponse(
            message=greeting_response,
            query_type=QueryType.GREETING
        )
    
    def _execute_with_fuzzy_fallback(self, sql: str, original_query: str) -> Tuple[List[Dict], str]:
        """
        Execute SQL with fuzzy search fallback if no results.
        Returns (results, final_sql_used)
        """
        try:
            results, _ = self.db.execute_query(sql)
            
            if results:
                return results, sql
            
            # No results - try fuzzy matching
            if DEBUG_MODE:
                print(f"[DEBUG] No results from SQL, attempting fuzzy search...")
            
            # Extract potential search terms from query
            search_terms = self._extract_search_terms(original_query)
            
            for term in search_terms:
                # Try department fuzzy search
                dept_results = self.db.fuzzy_search_departments(term, limit=5)
                if dept_results:
                    if DEBUG_MODE:
                        print(f"[DEBUG] Found departments via fuzzy search: {dept_results}")
                    
                    # Check if query looked like a specific course (e.g. "ENGL 104")
                    course_pattern = r'\b[a-zA-Z]{2,4}\s*\d{3}\b'
                    sql_desc = f"-- Fuzzy search for departments matching '{term}'"
                    
                    if re.search(course_pattern, original_query):
                        sql_desc += ". WARNING: User likely asked for a specific course, but ONLY the department was found. The course may NOT exist."
                        
                    return dept_results, sql_desc
                
                # Try course fuzzy search
                course_results = self.db.fuzzy_search_courses(term, limit=10)
                if course_results:
                    if DEBUG_MODE:
                        print(f"[DEBUG] Found courses via fuzzy search: {course_results}")
                    return course_results, f"-- Fuzzy search for courses matching '{term}'"
            
            return [], sql
            
        except RuntimeError as e:
            if DEBUG_MODE:
                print(f"[DEBUG] SQL execution error: {e}")
            raise
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from a query."""
        # Common words to ignore
        stop_words = {'the', 'a', 'an', 'is', 'are', 'what', 'which', 'who', 'where', 
                      'when', 'how', 'can', 'could', 'would', 'should', 'tell', 'me',
                      'about', 'for', 'in', 'on', 'at', 'to', 'of', 'and', 'or', 'i',
                      'want', 'need', 'find', 'show', 'list', 'get', 'give', 'all'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        
        # Filter and return non-stop words
        terms = [w for w in words if w not in stop_words]
        
        # Also check for course codes like "ICS 104" or "SWE205"
        course_codes = re.findall(r'\b[A-Z]{2,4}\s*\d{3}\b', query.upper())
        terms.extend(course_codes)
        
        # Also check for department shortcuts
        dept_shortcuts = re.findall(r'\b[A-Z]{2,4}\b', query.upper())
        terms.extend([s for s in dept_shortcuts if len(s) >= 2])
        
        return list(set(terms))
    
    def _format_results(self, results: List[Dict], original_query: str, sql_used: str) -> str:
        """Use LLM to format SQL results into a friendly response."""
        if not results:
            return self._get_no_results_message(original_query)
        
        formatting_prompt = get_result_formatting_prompt(results, original_query, sql_used)
        
        try:
            response = self.llm.generate(
                system_prompt="You are a helpful formatter. Convert database results into a clear, friendly response with markdown formatting.",
                user_message=formatting_prompt,
                temperature=0.5,
                max_tokens=1500
            )
            return response
        except Exception as e:
            # Fallback: simple formatting
            return self._simple_format_results(results)
    
    def _simple_format_results(self, results: List[Dict]) -> str:
        """Simple fallback formatting without LLM."""
        if not results:
            return "No results found."
        
        # Create a simple table
        if len(results) == 1:
            # Single result - format as bullet list
            item = results[0]
            lines = ["📋 **Result:**\n"]
            for key, value in item.items():
                if value:
                    lines.append(f"- **{key}**: {value}")
            return "\n".join(lines)
        
        # Multiple results - create table
        headers = list(results[0].keys())
        lines = [f"📊 Found {len(results)} results:\n"]
        
        # Table header
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Table rows (limit to 100)
        for row in results[:100]:
            values = [str(row.get(h, ""))[:50] for h in headers]  # Truncate long values
            lines.append("| " + " | ".join(values) + " |")
        
        if len(results) > 100:
            lines.append(f"\n*...and {len(results) - 100} more results*")
        
        return "\n".join(lines)
    
    def _get_no_results_message(self, query: str) -> str:
        """Generate a helpful no-results message."""
        return f"""🔍 I couldn't find any results matching your query.

**Suggestions:**
- Try different spelling or abbreviations (e.g., "ICS" instead of "Computer Science")
- Use broader search terms
- Ask about a specific course code (e.g., "ICS 104")

What else can I help you find?"""
    
    def process_query(self, query: str) -> AgentResponse:
        """
        Main entry point: Process a user query and return a response.
        
        Flow:
        1. Check if greeting -> respond without SQL
        2. Generate SQL from query
        3. Execute SQL with fuzzy fallback
        4. Format results into friendly response
        """
        query = query.strip()
        
        if not query:
            return AgentResponse(
                message="Please enter a question about KFUPM courses, departments, or degree plans.",
                query_type=QueryType.CLARIFICATION
            )
        
        # Quick greeting check
        if self._is_greeting(query):
            return self._handle_greeting(query)
        
        # Generate SQL using LLM
        try:
            llm_response = self.llm.generate(
                system_prompt=self.system_prompt,
                user_message=query,
                conversation_history=self.conversation_history[-6:],  # Last 3 exchanges
                temperature=0.3
            )
        except RuntimeError as e:
            return AgentResponse(
                message=f"⚠️ I'm having trouble connecting to my language model. Error: {str(e)}",
                query_type=QueryType.DATABASE_QUESTION,
                error=str(e)
            )
        
        # Check if LLM responded as greeting (even if we didn't catch it)
        if "I'm your KFUPM Course Advisor" in llm_response or "What would you like to know" in llm_response:
            return AgentResponse(
                message=llm_response,
                query_type=QueryType.GREETING
            )
        
        # Extract SQL from response
        sql = self._extract_sql(llm_response)
        
        if not sql:
            # LLM didn't generate SQL - might be conversational or out of scope
            if DEBUG_MODE:
                print(f"[DEBUG] No SQL extracted from response: {llm_response[:200]}...")
            return AgentResponse(
                message=llm_response if llm_response else "I'm not sure how to help with that. Could you rephrase your question about KFUPM courses or departments?",
                query_type=QueryType.OUT_OF_SCOPE
            )
        
        # Execute SQL with retry and fuzzy fallback
        for attempt in range(MAX_SQL_RETRIES + 1):
            try:
                results, final_sql = self._execute_with_fuzzy_fallback(sql, query)
                
                # Format results
                formatted_response = self._format_results(results, query, final_sql)
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": formatted_response})
                
                return AgentResponse(
                    message=formatted_response,
                    query_type=QueryType.DATABASE_QUESTION,
                    sql_used=final_sql,
                    raw_results=results
                )
                
            except (RuntimeError, ValueError) as e:
                if attempt < MAX_SQL_RETRIES:
                    if DEBUG_MODE:
                        print(f"[DEBUG] SQL attempt {attempt + 1} failed: {e}, retrying...")
                    # Try to get LLM to fix the SQL
                    fix_prompt = f"The SQL query failed with error: {e}\nOriginal query: {query}\nPlease generate a corrected SQL query."
                    llm_response = self.llm.generate(
                        system_prompt=self.system_prompt,
                        user_message=fix_prompt,
                        temperature=0.2
                    )
                    sql = self._extract_sql(llm_response)
                    if not sql:
                        break
                else:
                    return AgentResponse(
                        message=f"⚠️ I encountered an issue executing the database query. Please try rephrasing your question.\n\nTechnical details: {str(e)}",
                        query_type=QueryType.DATABASE_QUESTION,
                        sql_used=sql,
                        error=str(e)
                    )
        
        return AgentResponse(
            message="I had trouble processing your request. Could you try asking in a different way?",
            query_type=QueryType.DATABASE_QUESTION,
            error="Failed to execute SQL after retries"
        )
    
    def reset_history(self):
        """Clear conversation history."""
        self.conversation_history = []


# Singleton instance
_agent: Optional[CourseAdvisorAgent] = None

def get_agent() -> CourseAdvisorAgent:
    """Get the singleton agent instance."""
    global _agent
    if _agent is None:
        _agent = CourseAdvisorAgent()
    return _agent
