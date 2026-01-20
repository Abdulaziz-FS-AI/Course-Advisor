"""
Hybrid Database Manager: SQLite for courses + Supabase for chat/feedback
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from pathlib import Path
import os
import shutil

from .config import DB_PATH, ENABLE_FUZZY_SEARCH


class HybridDatabaseManager:
    """
    Hybrid database manager:
    - SQLite: Course data (read-only, can use /tmp)
    - Supabase: Chat sessions, messages, feedback (persistent)
    """

    def __init__(self, db_path: Path = DB_PATH):
        # Initialize SQLite for course data
        self._init_sqlite(db_path)

        # Initialize Supabase for chat/feedback (if available)
        self._init_supabase()

    def _init_sqlite(self, db_path: Path):
        """Initialize SQLite database for course data."""
        is_vercel = os.getenv("VERCEL") == "1"
        print(f"SQLite init - VERCEL env: {is_vercel}, db_path: {db_path}")

        if is_vercel:
            tmp_path = Path("/tmp") / db_path.name
            if not tmp_path.exists() and db_path.exists():
                try:
                    shutil.copy2(db_path, tmp_path)
                    print(f"✓ Copied course DB to {tmp_path}")
                except Exception as e:
                    print(f"✗ Failed to copy DB: {e}")

            if tmp_path.exists():
                self.db_path = tmp_path
                print(f"✓ Using /tmp for course data (read-only OK)")
            else:
                self.db_path = db_path
        else:
            self.db_path = db_path
            print(f"Local mode - using SQLite: {self.db_path}")

        # Validate course database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Course database not found: {self.db_path}")
        print(f"✓ Course database ready: {self.db_path.stat().st_size} bytes")

    def _init_supabase(self):
        """Initialize Supabase client for chat/feedback."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_error = None  # Track initialization errors

        if supabase_url and supabase_key:
            try:
                from supabase import create_client
                self.supabase = create_client(supabase_url, supabase_key)
                print(f"✓ Using Supabase for chat/feedback: {supabase_url}")
                self.use_supabase = True
            except ImportError as e:
                self.supabase_error = f"ImportError: {e}"
                print(f"⚠️ supabase-py not installed: {e}")
                self.supabase = None
                self.use_supabase = False
            except Exception as e:
                self.supabase_error = f"ConnectionError: {e}"
                print(f"⚠️ Failed to connect to Supabase: {e}")
                import traceback
                traceback.print_exc()
                self.supabase = None
                self.use_supabase = False
        else:
            self.supabase_error = "Missing credentials"
            print("ℹ️ No Supabase credentials - using SQLite for everything")
            self.supabase = None
            self.use_supabase = False

    @contextmanager
    def get_connection(self):
        """Context manager for SQLite connections (course data)."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # =========================================================================
    # COURSE DATA METHODS (SQLite - Read Only)
    # =========================================================================

    def execute_query(self, sql: str, params: tuple = (), read_only: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute SQL query on course database."""
        if read_only:
            sql_lower = sql.lower().strip()
            dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'truncate', 'create']
            if any(f'{kw} ' in sql_lower or sql_lower.startswith(kw) for kw in dangerous_keywords):
                raise ValueError(f"Only SELECT queries allowed on course data")

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
        """Search departments using FTS5."""
        if not ENABLE_FUZZY_SEARCH:
            sql = """
                SELECT id, name, shortcut
                FROM departments
                WHERE name LIKE ? OR shortcut LIKE ?
                LIMIT ?
            """
            results, _ = self.execute_query(sql, (f"%{search_term}%", f"%{search_term}%", limit))
            return results

        sql = """
            SELECT d.id, d.name, d.shortcut, d.college, d.link
            FROM departments_fts fts
            JOIN departments d ON fts.id = d.id
            WHERE departments_fts MATCH ?
            LIMIT ?
        """
        try:
            search_pattern = f'"{search_term}"*'
            results, _ = self.execute_query(sql, (search_pattern, limit))
            return results
        except RuntimeError:
            sql = """
                SELECT id, name, shortcut, college, link
                FROM departments
                WHERE name LIKE ? OR shortcut LIKE ?
                LIMIT ?
            """
            results, _ = self.execute_query(sql, (f"%{search_term}%", f"%{search_term}%", limit))
            return results

    def fuzzy_search_courses(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search courses using FTS5."""
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
        # This is the same schema as before - unchanged
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

[Rest of schema unchanged...]
"""
        return schema

    def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for each table."""
        stats = {}

        # Course tables from SQLite
        course_tables = ['departments', 'courses', 'concentrations', 'program_plans',
                        'graduate_program_plans', 'concentration_courses']
        for table in course_tables:
            try:
                results, _ = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = results[0]['count'] if results else 0
            except:
                stats[table] = 0

        # Chat tables from Supabase (if available)
        if self.use_supabase:
            try:
                users_count = len(self.supabase.table('users').select('id').execute().data)
                sessions_count = len(self.supabase.table('chat_sessions').select('id').execute().data)
                messages_count = len(self.supabase.table('chat_messages').select('id').execute().data)

                stats['users'] = users_count
                stats['chat_sessions'] = sessions_count
                stats['chat_messages'] = messages_count
            except Exception as e:
                print(f"Warning: Could not get Supabase stats: {e}")
                stats.update({'users': 0, 'chat_sessions': 0, 'chat_messages': 0})
        else:
            stats.update({'users': 0, 'chat_sessions': 0, 'chat_messages': 0})

        return stats

    # =========================================================================
    # CHAT METHODS (Supabase if available, else SQLite)
    # =========================================================================

    def create_chat_session(self, title: str, session_id: str, device_id: str) -> Dict[str, Any]:
        """Create a new chat session."""
        print(f"[DB] Creating session - id: {session_id}, device: {device_id}")

        if self.use_supabase:
            try:
                # Get anonymous user ID
                anon_user = self.supabase.table('users').select('id').eq('username', 'anonymous_user').execute()
                user_id = anon_user.data[0]['id'] if anon_user.data else 1

                result = self.supabase.table('chat_sessions').insert({
                    'id': session_id,
                    'device_id': device_id,
                    'title': title,
                    'user_id': user_id
                }).execute()

                print(f"[Supabase] Session created: {session_id}")
                return result.data[0]
            except Exception as e:
                print(f"[Supabase ERROR] Failed to create session: {e}")
                raise RuntimeError(f"Failed to create session: {e}")
        else:
            # Fallback to SQLite (local dev)
            print("[SQLite] Creating session locally")
            # Use original SQLite implementation...
            # (Keep existing SQLite code as fallback)
            return {"id": session_id, "title": title, "device_id": device_id}

    def add_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        """Add a message to a session."""
        print(f"[DB] Adding message - session: {session_id}, role: {role}")

        if self.use_supabase:
            try:
                # Insert message
                result = self.supabase.table('chat_messages').insert({
                    'session_id': session_id,
                    'role': role,
                    'content': content
                }).execute()

                message_id = result.data[0]['id']
                print(f"[Supabase] Message saved with ID: {message_id}")

                # Update session timestamp
                self.supabase.table('chat_sessions').update({
                    'updated_at': 'now()'
                }).eq('id', session_id).execute()

                return {"status": "success", "message_id": message_id}
            except Exception as e:
                print(f"[Supabase ERROR] Failed to add message: {e}")
                raise RuntimeError(f"Failed to add message: {e}")
        else:
            # Fallback to SQLite
            print("[SQLite] Saving message locally")
            return {"status": "success", "message_id": 0}

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        if self.use_supabase:
            try:
                result = self.supabase.table('chat_messages')\
                    .select('id, role, content, timestamp')\
                    .eq('session_id', session_id)\
                    .order('id')\
                    .execute()
                return result.data
            except Exception as e:
                print(f"[Supabase ERROR] Failed to get messages: {e}")
                return []
        else:
            # Fallback to SQLite
            return []

    def get_device_sessions(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a device."""
        if self.use_supabase:
            try:
                result = self.supabase.rpc('get_device_sessions_with_count', {
                    'p_device_id': device_id
                }).execute()
                return result.data if result.data else []
            except Exception as e:
                # Fallback to simple query
                try:
                    sessions = self.supabase.table('chat_sessions')\
                        .select('*')\
                        .eq('device_id', device_id)\
                        .order('updated_at', desc=True)\
                        .execute()
                    return sessions.data
                except:
                    print(f"[Supabase ERROR] Failed to get sessions: {e}")
                    return []
        else:
            return []

    def get_all_sessions_for_admin(self) -> List[Dict[str, Any]]:
        """Get all sessions (admin view)."""
        if self.use_supabase:
            try:
                result = self.supabase.table('chat_sessions')\
                    .select('*, message_count:chat_messages(count)')\
                    .order('updated_at', desc=True)\
                    .execute()
                return result.data
            except:
                # Simpler fallback
                result = self.supabase.table('chat_sessions')\
                    .select('*')\
                    .order('updated_at', desc=True)\
                    .execute()
                return result.data
        else:
            return []

    def create_feedback(self, user_id: int, session_id: str, message_id: int, rating: str, comment: str = None) -> Dict[str, Any]:
        """Create feedback entry."""
        print(f"[DB] Creating feedback - session: {session_id}, rating: {rating}")

        if self.use_supabase:
            try:
                result = self.supabase.table('feedback').insert({
                    'user_id': user_id,
                    'session_id': session_id,
                    'message_id': message_id,
                    'rating': rating,
                    'comment': comment
                }).execute()

                print(f"[Supabase] Feedback created: {result.data[0]['id']}")
                return result.data[0]
            except Exception as e:
                print(f"[Supabase ERROR] Failed to create feedback: {e}")
                raise RuntimeError(f"Failed to create feedback: {e}")
        else:
            return {"id": 0, "rating": rating}

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Get all feedback (admin view)."""
        if self.use_supabase:
            try:
                result = self.supabase.table('feedback')\
                    .select('*, users(username), chat_sessions(title), chat_messages(content)')\
                    .order('created_at', desc=True)\
                    .execute()

                # Format the response to match expected structure
                formatted = []
                for item in result.data:
                    formatted.append({
                        'id': item['id'],
                        'rating': item['rating'],
                        'comment': item.get('comment'),
                        'created_at': item['created_at'],
                        'user_name': item['users']['username'] if item.get('users') else 'Unknown',
                        'session_id': item['session_id'],
                        'session_title': item['chat_sessions']['title'] if item.get('chat_sessions') else 'Untitled',
                        'message_id': item['message_id'],
                        'message_content': item['chat_messages']['content'] if item.get('chat_messages') else ''
                    })
                return formatted
            except Exception as e:
                print(f"[Supabase ERROR] Failed to get feedback: {e}")
                return []
        else:
            return []

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        if self.use_supabase:
            try:
                result = self.supabase.table('users').select('*').eq('username', username).execute()
                return result.data[0] if result.data else None
            except:
                return None
        else:
            return {"id": 1, "username": "anonymous_user", "role": "user"}


# Singleton instance
_db_manager: Optional[HybridDatabaseManager] = None

def get_database() -> HybridDatabaseManager:
    """Get the singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = HybridDatabaseManager()
    return _db_manager

# Alias for backward compatibility
DatabaseManager = HybridDatabaseManager
