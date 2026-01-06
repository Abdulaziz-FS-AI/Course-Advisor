"""
Smart KFUPM Course Advisor Agent.
Uses LLM to intelligently handle all queries - no hardcoded patterns.
Flow: Query → LLM decides (direct response OR SQL) → Execute if SQL → Format response
"""

import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from .config import MAX_SQL_RETRIES, DEBUG_MODE, LLM_TEMPERATURE, LLM_MAX_TOKENS
from .database import get_database, DatabaseManager
from .llm_client import get_llm_client, LLMClient
from .system_prompt import get_system_prompt, get_result_formatting_prompt


@dataclass
class AgentResponse:
    """Structured response from the agent."""
    message: str
    sql_used: Optional[str] = None
    raw_results: Optional[List[Dict]] = None
    error: Optional[str] = None


class CourseAdvisorAgent:
    """
    Smart agent for handling course advising queries.

    The LLM handles ALL decisions:
    - Greetings → Direct response
    - Database questions → Generate SQL
    - Clarifications → Direct response
    - Out of scope → Polite redirect
    """

    def __init__(self):
        self.db: DatabaseManager = get_database()
        self.llm: LLMClient = get_llm_client()
        self.system_prompt = get_system_prompt()

    def _extract_sql(self, llm_response: str) -> Optional[str]:
        """Extract SQL query from LLM response if present."""
        # Try JSON format first (preferred)
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, dict) and "sql" in data:
                    return data["sql"].strip()
            except json.JSONDecodeError:
                pass

        # Try SQL code block
        sql_match = re.search(r'```sql\s*(.*?)\s*```', llm_response, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()

        # Try raw SELECT statement (must end with semicolon for safety)
        select_match = re.search(r'(SELECT\s+.+?;)', llm_response, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()

        return None

    def _is_direct_response(self, llm_response: str) -> bool:
        """Check if LLM gave a direct response (no SQL needed)."""
        # If there's no SQL in the response, it's a direct response
        return self._extract_sql(llm_response) is None

    def _clean_direct_response(self, response: str) -> str:
        """Clean up a direct response from LLM."""
        # Remove any JSON blocks that might have slipped through
        response = re.sub(r'```json\s*.*?\s*```', '', response, flags=re.DOTALL)
        response = re.sub(r'```sql\s*.*?\s*```', '', response, flags=re.DOTALL)
        return response.strip()

    def _execute_sql(self, sql: str) -> Tuple[List[Dict], Optional[str]]:
        """Execute SQL query and return results."""
        try:
            results, _ = self.db.execute_query(sql)
            return results, None
        except Exception as e:
            return [], str(e)

    def _format_results(self, results: List[Dict], original_query: str, sql_used: str) -> str:
        """Use LLM to format SQL results into a friendly response."""
        if not results:
            return "I couldn't find any results matching your query. Try rephrasing or using different terms."

        formatting_prompt = get_result_formatting_prompt(results, original_query, sql_used)

        try:
            response = self.llm.generate(
                system_prompt="You are a helpful assistant. Format database results into clear, friendly responses with markdown. Be concise and factual.",
                user_message=formatting_prompt,
                temperature=0.4,
                max_tokens=2000
            )
            return response
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Formatting error: {e}")
            return self._simple_format_results(results)

    def _simple_format_results(self, results: List[Dict]) -> str:
        """Fallback formatting without LLM."""
        if not results:
            return "No results found."

        if len(results) == 1:
            item = results[0]
            lines = []
            for key, value in item.items():
                if value is not None and value != "":
                    lines.append(f"**{key}**: {value}")
            return "\n".join(lines)

        # Multiple results - create table
        headers = list(results[0].keys())
        lines = [f"Found {len(results)} results:\n"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in results[:50]:  # Limit to 50 rows
            values = [str(row.get(h, ""))[:40] for h in headers]
            lines.append("| " + " | ".join(values) + " |")

        if len(results) > 50:
            lines.append(f"\n*...and {len(results) - 50} more results*")

        return "\n".join(lines)

    def process_query(self, query: str, history: List[Dict] = None) -> AgentResponse:
        """
        Process a user query intelligently.

        Flow:
        1. Send query to LLM with system prompt
        2. LLM decides: direct response OR SQL query
        3. If SQL: execute and format results
        4. Return final response
        """
        query = query.strip()
        history = history or []

        if not query:
            return AgentResponse(
                message="Please enter a question about KFUPM courses, departments, or degree plans."
            )

        # Step 1: Let LLM analyze the query and decide how to respond
        try:
            llm_response = self.llm.generate(
                system_prompt=self.system_prompt,
                user_message=query,
                conversation_history=history[-6:],
                temperature=0.1,  # Very low for accurate SQL generation
                max_tokens=LLM_MAX_TOKENS
            )
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] LLM error: {e}")
            return AgentResponse(
                message="I'm having trouble processing your request. Please try again.",
                error=str(e)
            )

        if DEBUG_MODE:
            print(f"[DEBUG] LLM Response: {llm_response[:500]}...")

        # Step 2: Check if LLM generated SQL or gave direct response
        sql = self._extract_sql(llm_response)

        if not sql:
            # Direct response from LLM (greeting, clarification, out of scope)
            clean_response = self._clean_direct_response(llm_response)
            return AgentResponse(
                message=clean_response if clean_response else "I'm not sure how to help with that. Try asking about KFUPM courses, departments, or degree plans."
            )

        # Step 3: Execute SQL with retries
        last_error = None
        for attempt in range(MAX_SQL_RETRIES + 1):
            results, error = self._execute_sql(sql)

            if error is None:
                # Success - format and return
                formatted = self._format_results(results, query, sql)
                return AgentResponse(
                    message=formatted,
                    sql_used=sql,
                    raw_results=results
                )

            last_error = error

            if attempt < MAX_SQL_RETRIES:
                if DEBUG_MODE:
                    print(f"[DEBUG] SQL attempt {attempt + 1} failed: {error}")

                # Ask LLM to fix the SQL
                fix_prompt = f"""The SQL query failed with error: {error}

Original user question: {query}
Failed SQL: {sql}

Generate a corrected SQL query to answer the user's question."""

                try:
                    fix_response = self.llm.generate(
                        system_prompt=self.system_prompt,
                        user_message=fix_prompt,
                        temperature=0.1,
                        max_tokens=1000
                    )
                    new_sql = self._extract_sql(fix_response)
                    if new_sql:
                        sql = new_sql
                    else:
                        break
                except Exception:
                    break

        # All retries failed
        return AgentResponse(
            message="I had trouble finding that information. Could you try rephrasing your question?",
            sql_used=sql,
            error=last_error
        )


# Singleton instance
_agent: Optional[CourseAdvisorAgent] = None

def get_agent() -> CourseAdvisorAgent:
    """Get the singleton agent instance."""
    global _agent
    if _agent is None:
        _agent = CourseAdvisorAgent()
    return _agent
