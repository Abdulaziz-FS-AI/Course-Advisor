"""
Database utilities for KFUPM Course Advisor Agent.
Handles SQLite connection, query execution, and fuzzy search with FTS5.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from pathlib import Path

from .config import DB_PATH, ENABLE_FUZZY_SEARCH


class DatabaseManager:
    """Manages SQLite database connections and queries."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._validate_database()
    
    def _validate_database(self):
        """Ensure database file exists."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, sql: str, params: tuple = ()) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute SQL query safely and return results.
        
        Returns:
            Tuple of (rows as list of dicts, column names)
        """
        # Security: Block dangerous operations
        sql_lower = sql.lower().strip()
        dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'truncate', 'create']
        if any(f'{kw} ' in sql_lower or sql_lower.startswith(kw) for kw in dangerous_keywords):
            raise ValueError(f"Dangerous SQL operation detected. Only SELECT queries are allowed.")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in rows], columns
        except sqlite3.Error as e:
            raise RuntimeError(f"SQL execution error: {e}")
    
    def fuzzy_search_departments(self, search_term: str, limit: int = 5) -> List[Dict]:
        """
        Search departments using FTS5 trigram matching.
        Handles partial matches and typos.
        """
        if not ENABLE_FUZZY_SEARCH:
            # Fallback to LIKE
            sql = """
                SELECT id, name, shortcut 
                FROM departments 
                WHERE name LIKE ? OR shortcut LIKE ?
                LIMIT ?
            """
            results, _ = self.execute_query(sql, (f"%{search_term}%", f"%{search_term}%", limit))
            return results
        
        # FTS5 search with trigram tokenizer
        sql = """
            SELECT d.id, d.name, d.shortcut, d.college, d.link
            FROM departments_fts fts
            JOIN departments d ON fts.id = d.id
            WHERE departments_fts MATCH ?
            LIMIT ?
        """
        try:
            # Add wildcards for partial matching
            search_pattern = f'"{search_term}"*'
            results, _ = self.execute_query(sql, (search_pattern, limit))
            return results
        except RuntimeError:
            # Fallback to LIKE if FTS fails
            sql = """
                SELECT id, name, shortcut, college, link 
                FROM departments 
                WHERE name LIKE ? OR shortcut LIKE ?
                LIMIT ?
            """
            results, _ = self.execute_query(sql, (f"%{search_term}%", f"%{search_term}%", limit))
            return results
    
    def fuzzy_search_courses(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search courses using FTS5 trigram matching.
        Handles partial code and title matches.
        """
        if not ENABLE_FUZZY_SEARCH:
            sql = """
                SELECT id, code, title, credits 
                FROM courses 
                WHERE code LIKE ? OR title LIKE ?
                LIMIT ?
            """
            results, _ = self.execute_query(sql, (f"%{search_term}%", f"%{search_term}%", limit))
            return results
        
        sql = """
            SELECT c.id, c.code, c.title, c.credits, c.description, c.prerequisites
            FROM courses_fts fts
            JOIN courses c ON fts.id = c.id
            WHERE courses_fts MATCH ?
            LIMIT ?
        """
        try:
            search_pattern = f'"{search_term}"*'
            results, _ = self.execute_query(sql, (search_pattern, limit))
            return results
        except RuntimeError:
            sql = """
                SELECT id, code, title, credits, description, prerequisites
                FROM courses 
                WHERE code LIKE ? OR title LIKE ?
                LIMIT ?
            """
            results, _ = self.execute_query(sql, (f"%{search_term}%", f"%{search_term}%", limit))
            return results
    
    def get_schema_info(self) -> str:
        """Get database schema description for LLM context."""
        schema = """
## Database Tables

### departments
- id (INTEGER, PRIMARY KEY)
- name (TEXT) - Full department name, e.g., "Information and Computer Science"
- shortcut (TEXT, UNIQUE) - Abbreviation, e.g., "ICS", "SWE", "COE"
- college (TEXT) - Parent college name
- link (TEXT) - Official department website URL (ALWAYS include in responses about departments)

### courses
- id (INTEGER, PRIMARY KEY)
- code (TEXT, UNIQUE) - Course code, e.g., "ICS 104", "SWE 205"
- title (TEXT) - Course title
- lecture_hours (INTEGER)
- lab_hours (INTEGER)
- credits (INTEGER)
- department_id (INTEGER, FK -> departments.id)
- type (TEXT) - "Undergraduate" or "Graduate"
- description (TEXT) - Course description
- prerequisites (TEXT) - Prerequisite courses

### concentrations
- id (INTEGER, PRIMARY KEY)
- name (TEXT) - Concentration name, e.g., "Artificial Intelligence and Machine Learning"
- description (TEXT) - Full description
- department_id (INTEGER, FK -> departments.id)

### program_plans (Degree Plans)
- id (INTEGER, PRIMARY KEY)
- department_id (INTEGER, FK)
- year_level (INTEGER) - 1=Freshman, 2=Sophomore, 3=Junior, 4=Senior, 5=Graduate
- semester (INTEGER) - 1 or 2
- course_id (INTEGER, FK -> courses.id)
- course_code (TEXT)
- course_title (TEXT)
- credits (INTEGER)
- plan_option (TEXT) - "0"=Core, "1"=Coop, "2"=Summer Training
- plan_type (TEXT) - "Undergraduate" or "Graduate"

### concentration_courses
- id (INTEGER, PRIMARY KEY)
- concentration_id (INTEGER, FK)
- course_id (INTEGER, FK)
- course_code (TEXT)
- course_title (TEXT)
- description (TEXT)
- prerequisites (TEXT)
- semester (TEXT)

## Key Relationships
- courses.department_id -> departments.id
- concentrations.department_id -> departments.id
- program_plans.department_id -> departments.id
- concentration_courses.concentration_id -> concentrations.id
"""
        return schema
    
    def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for each table."""
        tables = ['departments', 'courses', 'concentrations', 'program_plans', 'concentration_courses']
        stats = {}
        for table in tables:
            results, _ = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = results[0]['count'] if results else 0
        return stats


# Singleton instance
_db_manager: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    """Get the singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
