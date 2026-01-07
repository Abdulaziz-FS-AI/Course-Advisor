"""
Database utilities for KFUPM Course Advisor Agent.
Handles SQLite connection, query execution, and fuzzy search with FTS5.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from pathlib import Path
import os
import shutil

from .config import DB_PATH, ENABLE_FUZZY_SEARCH


class DatabaseManager:
    """Manages SQLite database connections and queries."""
    
    def __init__(self, db_path: Path = DB_PATH):
        # Vercel Read-Only Fix: Copy DB to /tmp if running on Vercel (or if we can't write to source)
        # Check if VERCEL env var is set
        is_vercel = os.getenv("VERCEL") == "1"
        print(f"DatabaseManager init - VERCEL env: {is_vercel}, db_path: {db_path}")

        if is_vercel:
            tmp_path = Path("/tmp") / db_path.name
            print(f"Vercel mode - tmp_path: {tmp_path}, exists: {tmp_path.exists()}")
            print(f"Source db_path exists: {db_path.exists()}")

            if not tmp_path.exists() and db_path.exists():
                try:
                    shutil.copy2(db_path, tmp_path)
                    print(f"✓ Copied DB to {tmp_path} (size: {tmp_path.stat().st_size} bytes)")
                except Exception as e:
                    print(f"✗ Failed to copy DB to tmp: {e}")
                    import traceback
                    traceback.print_exc()

            # Use tmp path if it exists now
            if tmp_path.exists():
                self.db_path = tmp_path
                print(f"✓ Using tmp DB path: {self.db_path}")
            else:
                self.db_path = db_path
                print(f"⚠ Falling back to source DB path: {self.db_path}")
        else:
            self.db_path = db_path
            print(f"Local mode - using db_path: {self.db_path}")

        self._validate_database()
    
    def _validate_database(self):
        """Ensure database file exists."""
        if not self.db_path.exists():
            error_msg = f"Database not found: {self.db_path}"
            print(f"✗ Database validation failed: {error_msg}")
            # List parent directory contents for debugging
            if self.db_path.parent.exists():
                print(f"Parent dir exists. Contents: {list(self.db_path.parent.iterdir())}")
            else:
                print(f"Parent dir does not exist: {self.db_path.parent}")
            raise FileNotFoundError(error_msg)
        print(f"✓ Database validated: {self.db_path} (size: {self.db_path.stat().st_size} bytes)")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, sql: str, params: tuple = (), read_only: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute SQL query safely and return results.
        
        Args:
            read_only: If True, blocks modification queries.
        
        Returns:
            Tuple of (rows as list of dicts, column names)
        """
        # Security: Block dangerous operations if read_only
        if read_only:
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
                results = [dict(zip(columns, row)) for row in rows]

                if not read_only:
                    conn.commit()
                
                return results, columns
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
## TABLES & COLUMNS

### departments
The central reference table. All other tables link here via department_id.
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Full department name (e.g., "Information and Computer Science") |
| shortcut | TEXT | 2-4 letter code used in course codes (e.g., "ICS", "SWE") |
| college | TEXT | Parent college name |
| other_info | TEXT | Additional department information (may be empty) |
| link | TEXT | Official department website URL |

### courses
All undergraduate and graduate courses offered at KFUPM.
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| code | TEXT | Course code like "ICS 104", "SWE 205" |
| title | TEXT | Course name |
| lecture_hours | INTEGER | Weekly lecture hours |
| lab_hours | INTEGER | Weekly lab hours |
| credits | INTEGER | Credit hours |
| department_id | INTEGER | FK → departments.id |
| type | TEXT | "Undergraduate" or "Graduate" |
| description | TEXT | Full course description |
| prerequisites | TEXT | ~58% populated - check this field first for prerequisite queries |

### program_plans
Degree curriculum for each major (semester-by-semester course sequence).
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| department_id | INTEGER | FK → departments.id (which major this plan is for) |
| year_level | INTEGER | 1=Freshman (387), 2=Sophomore (404), 3=Junior (383), 4=Senior (171), 5=Graduate (785) |
| semester | INTEGER | 1 or 2 (Fall/Spring) |
| course_id | INTEGER | FK → courses.id |
| course_code | TEXT | Course code (denormalized for convenience) |
| course_title | TEXT | Course title (denormalized) |
| lecture_hours | INTEGER | Weekly lecture hours for this course |
| lab_hours | INTEGER | Weekly lab hours for this course |
| credits | INTEGER | Credit hours |
| plan_option | TEXT | "0"=Core (1298 rows), "1"=Co-op (314 rows), "2"=Summer (518 rows). Usually use "0" for standard plan. |
| plan_type | TEXT | ⚠️ CRITICAL: "Undergraduate" or "Graduate" - ALWAYS filter by this! |

### concentrations
Interdisciplinary specialization tracks students can pursue.
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Concentration name (e.g., "Artificial Intelligence and Machine Learning") |
| description | TEXT | Full description of the concentration |
| department_id | INTEGER | FK → departments.id (who HOSTS/RUNS this concentration) |
| offered_to | TEXT | ⚠️ CRITICAL: Comma-separated majors who CAN TAKE it (e.g., "COE, CS, SWE") |

**⚠️ IMPORTANT DISTINCTION:**
- `department_id` = Which department HOSTS the concentration
- `offered_to` = Which majors are ELIGIBLE to enroll
- Query "concentrations for AE students" → `WHERE offered_to LIKE '%AE%'`
- Query "concentrations run by AE dept" → `WHERE department_id = AE_id`

### concentration_courses
Courses that belong to each concentration track.
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| concentration_id | INTEGER | FK → concentrations.id |
| course_id | INTEGER | FK → courses.id |
| course_code | TEXT | Course code |
| course_title | TEXT | Course title |
| description | TEXT | Course description |
| prerequisites | TEXT | Complete for concentration courses (168 rows total) |
| semester | INTEGER | Suggested semester to take |

## KEY RULES

1. **Always JOIN departments** to get the website link:
   `SELECT c.*, d.name as dept_name, d.link FROM courses c JOIN departments d ON c.department_id = d.id`

2. **Department matching** - be flexible with both shortcut and name:
   `WHERE LOWER(d.shortcut) = LOWER('ICS') OR LOWER(d.name) LIKE '%computer%'`

3. **Degree plans** - ALWAYS filter by plan_type:
   `WHERE plan_type = 'Undergraduate'` or `WHERE plan_type = 'Graduate'`

4. **Concentrations for a major** - use offered_to, NOT department_id:
   `WHERE offered_to LIKE '%SWE%'` (finds all concentrations SWE students can take)

5. **Prerequisites** - use courses.prerequisites (58% populated); concentration_courses only has 168 rows

6. **Concentration details** - ALWAYS include courses via JOIN:
   When asked about a specific concentration, JOIN with `concentration_courses` to show the required courses.
   Users expect to see what courses make up that concentration!

7. **CS vs ICS - BOTH are valid, different data:**
   - ICS (ID=49) ← Has 157 plans, 137 courses (use for degree plans/courses)
   - CS (ID=25) ← Has 2 concentrations (AI/ML, Cybersecurity)
   For "Computer Science" queries, search BOTH: `WHERE d.shortcut IN ('ICS', 'CS')`

8. **Graduate plans have NULL semester**: All 785 graduate plan rows have semester=NULL.
   Don't rely on semester ordering for graduate plans.

9. **22 departments have NO program_plans**: SE (130 courses), BIOE (65), MGT (54), STAT (54), CP (38),
   OM (37), ECON (32), GS (24), HRM (24), IAS (20), DATA (14), ESE (9), PE (7), BIOL (6), BUS (6),
   CPG (5), ENTR (5), ENGL (4), GEO (3), CS (1), CGS (1), MM (0).
   If no plan results, inform the user that this department's degree plan is not in the database.
"""
        return schema
    
    def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for each table."""
        tables = ['departments', 'courses', 'concentrations', 'program_plans', 
                 'graduate_program_plans', 'concentration_courses', 'users', 'chat_sessions', 'chat_messages']
        stats = {}
        for table in tables:
            try:
                results, _ = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = results[0]['count'] if results else 0
            except:
                stats[table] = 0
        return stats

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def create_user(self, username: str, password_hash: str, role: str = 'user') -> Dict[str, Any]:
        """Create a new user."""
        sql = """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            RETURNING id, username, role, created_at
        """
        try:
            results, _ = self.execute_query(sql, (username, password_hash, role), read_only=False)
            return results[0]
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("Username already exists")
            raise e

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        sql = "SELECT * FROM users WHERE username = ?"
        results, _ = self.execute_query(sql, (username,))
        return results[0] if results else None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (for admin)."""
        sql = """
            SELECT u.id, u.username, u.role, u.created_at, 
                   COUNT(cs.id) as session_count,
                   (SELECT COUNT(*) FROM chat_messages cm JOIN chat_sessions cs2 ON cm.session_id = cs2.id WHERE cs2.user_id = u.id) as message_count
            FROM users u
            LEFT JOIN chat_sessions cs ON u.id = cs.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """
        # Admin queries are read-only
        results, _ = self.execute_query(sql)
        return results

    # =========================================================================
    # CHAT MANAGEMENT
    # =========================================================================

    # =========================================================================
    # ANONYMOUS SESSION MANAGEMENT
    # =========================================================================

    def create_chat_session(self, title: str, session_id: str, device_id: str) -> Dict[str, Any]:
        """Create a new anonymous chat session linked to a device ID."""
        
        # Ensure 'device_id' column exists (migration helper)
        self._ensure_device_column()
        
        # Get or create anonymous user to satisfy foreign key constraint
        anon_user = self.get_user_by_username("anonymous_user")
        if not anon_user:
            try:
                # Create with dummy hash
                self.create_user("anonymous_user", "nopassword", role="user")
                anon_user = self.get_user_by_username("anonymous_user")
            except:
                pass
        
        user_id = anon_user["id"] if anon_user else 1 # Fallback to admin if query fails
            
        sql = """
            INSERT INTO chat_sessions (id, device_id, title, user_id)
            VALUES (?, ?, ?, ?)
            RETURNING id, device_id, title, created_at
        """
        
        results, _ = self.execute_query(sql, (session_id, device_id, title, user_id), read_only=False)
        return results[0]


    def get_device_sessions(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a specific device."""
        self._ensure_device_column()
        sql = """
            SELECT cs.*, COUNT(cm.id) as message_count
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            WHERE cs.device_id = ?
            GROUP BY cs.id
            ORDER BY cs.updated_at DESC
        """
        results, _ = self.execute_query(sql, (device_id,))
        return results

    def get_all_sessions_for_admin(self) -> List[Dict[str, Any]]:
        """Get ALL sessions (for admin dashboard)."""
        self._ensure_device_column()
        sql = """
            SELECT cs.*, COUNT(cm.id) as message_count
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            GROUP BY cs.id
            ORDER BY cs.updated_at DESC
        """
        results, _ = self.execute_query(sql)
        return results

    def _ensure_device_column(self):
        """Helper to migrate schema on the fly if needed."""
        try:
            self.execute_query("SELECT device_id FROM chat_sessions LIMIT 1")
        except:
            # Column doesn't exist, add it
            try:
                self.execute_query("ALTER TABLE chat_sessions ADD COLUMN device_id TEXT", read_only=False)
                self.execute_query("CREATE INDEX idx_device_id ON chat_sessions(device_id)", read_only=False)
            except Exception as e:
                print(f"Migration warning: {e}")


    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user with message counts."""
        sql = """
            SELECT cs.*, COUNT(cm.id) as message_count
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            WHERE cs.user_id = ?
            GROUP BY cs.id
            ORDER BY cs.updated_at DESC
        """
        results, _ = self.execute_query(sql, (user_id,))
        return results

    def add_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        """Add a message to a session and return the message ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Insert message
                cursor.execute("""
                    INSERT INTO chat_messages (session_id, role, content)
                    VALUES (?, ?, ?)
                """, (session_id, role, content))

                message_id = cursor.lastrowid

                # Update session timestamp
                cursor.execute("""
                    UPDATE chat_sessions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (session_id,))

                conn.commit()
                return {"status": "success", "message_id": message_id}
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        sql = """
            SELECT role, content, timestamp 
            FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY id ASC
        """
        results, _ = self.execute_query(sql, (session_id,))
        return results
    # =========================================================================
    # FEEDBACK MANAGEMENT
    # =========================================================================

    def _ensure_feedback_table(self):
        """Create feedback table if it does not exist."""
        sql = """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                session_id TEXT,
                message_id INTEGER REFERENCES chat_messages(id),
                rating TEXT CHECK(rating IN ('up','down')),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.execute_query(sql, (), read_only=False)

    def create_feedback(self, user_id: int, session_id: str, message_id: int, rating: str, comment: str = None) -> Dict[str, Any]:
        """Insert a feedback entry. rating must be 'up' or 'down'."""
        self._ensure_feedback_table()
        sql = """
            INSERT INTO feedback (user_id, session_id, message_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (user_id, session_id, message_id, rating, comment)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                feedback_id = cursor.lastrowid
                # Return the created feedback
                cursor.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
                row = cursor.fetchone()
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to create feedback: {e}")

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Return all feedback with related user, session, and message info."""
        self._ensure_feedback_table()
        sql = """
            SELECT f.id, f.rating, f.comment, f.created_at,
                   u.username AS user_name,
                   s.id AS session_id, s.title AS session_title,
                   m.id AS message_id, m.role AS message_role, m.content AS message_content
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            JOIN chat_sessions s ON f.session_id = s.id
            JOIN chat_messages m ON f.message_id = m.id
            ORDER BY f.created_at DESC;
        """
        results, _ = self.execute_query(sql)
        return results


# Singleton instance
_db_manager: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    """Get the singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
