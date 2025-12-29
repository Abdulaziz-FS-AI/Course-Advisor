import pandas as pd
import psycopg2
from psycopg2 import extras
import os
import re

# --- Configuration ---
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres.xieihyzyidrppjtzmzvy",
    "password": "Itsmemario@747",
    "host": "aws-1-ap-northeast-2.pooler.supabase.com",
    "port": "5432",
    "sslmode": "require",
    "connect_timeout": 10
}

CSV_PATHS = {
    "departments": "/home/shared_dir/data/SQL/departments.csv",
    "courses": "/home/shared_dir/data/SQL/courses.csv",
    "concentrations": "/home/shared_dir/data/SQL/concentrations.csv",
    "concentration_courses": "/home/shared_dir/data/SQL/concentration_courses.csv",
    "program_plans": "/home/shared_dir/data/SQL/program_plans_organized.csv",
    "graduate_program_plans": "/home/shared_dir/data/SQL/graduate_program_plans.csv"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def extract_department_shortcut(course_code):
    match = re.match(r'^([A-Z]+)', str(course_code))
    if match:
        return match.group(1)
    return None

def migrate():
    print("Connecting to database...")
    conn = get_connection()
    print("Connected!")
    cur = conn.cursor()
    
    print("Creating tables if not exists...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            shortcut TEXT UNIQUE,
            college TEXT,
            other_info TEXT,
            link TEXT
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE,
            title TEXT,
            lecture_hours INTEGER,
            lab_hours INTEGER,
            credits INTEGER,
            department_id INTEGER,
            type TEXT,
            description TEXT,
            prerequisites TEXT
        );
        CREATE TABLE IF NOT EXISTS concentrations (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            department_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS concentration_departments (
            concentration_id INTEGER,
            department_id INTEGER,
            PRIMARY KEY (concentration_id, department_id)
        );
        CREATE TABLE IF NOT EXISTS program_plans (
            id INTEGER PRIMARY KEY,
            department_id INTEGER,
            year_level INTEGER,
            semester INTEGER,
            course_id INTEGER,
            course_code TEXT,
            course_title TEXT,
            lecture_hours INTEGER,
            lab_hours INTEGER,
            credits INTEGER,
            plan_option TEXT,
            plan_type TEXT
        );
        CREATE TABLE IF NOT EXISTS concentration_courses (
            id INTEGER PRIMARY KEY, -- Use SERIAL in production if auto-inc is needed, here explicit IDs are loaded
            concentration_id INTEGER,
            course_id INTEGER,
            course_code TEXT,
            course_title TEXT,
            description TEXT,
            prerequisites TEXT,
            semester INTEGER
        );
    """)
    
    print("Deleting existing data (Trimming for a clean start)...")
    cur.execute("TRUNCATE departments, courses, concentrations, concentration_departments, program_plans, concentration_courses CASCADE;")
    conn.commit()

    # 1. Departments
    print("Loading departments...")
    df_dept = load_csv(CSV_PATHS["departments"])
    if df_dept is not None:
        values = [tuple(x) for x in df_dept[['id', 'name', 'shortcut', 'college', 'other_info', 'link']].values]
        extras.execute_values(cur, "INSERT INTO departments (id, name, shortcut, college, other_info, link) VALUES %s ON CONFLICT (id) DO NOTHING", values)
    conn.commit()

    # Create mapping for department shortcuts to IDs
    cur.execute("SELECT shortcut, id FROM departments")
    dept_map = dict(cur.fetchall())

    # 2. Courses (Initial load from catalog)
    print("Loading courses from catalog...")
    df_catalog = load_csv(CSV_PATHS["courses"])
    if df_catalog is not None:
        values = []
        for _, row in df_catalog.iterrows():
            values.append((
                int(row['id']),
                row['code'],
                row['title'],
                int(row['lecture_hours']) if pd.notna(row['lecture_hours']) else None,
                int(row['lab_hours']) if pd.notna(row['lab_hours']) else None,
                int(row['credits']) if pd.notna(row['credits']) else None,
                int(row['department_id']) if pd.notna(row['department_id']) else None,
                row['type'],
                row['description'],
                row['prerequisites']
            ))
        extras.execute_values(cur, """
            INSERT INTO courses (id, code, title, lecture_hours, lab_hours, credits, department_id, type, description, prerequisites) 
            VALUES %s ON CONFLICT (id) DO NOTHING
        """, values)
    conn.commit()

    # 3. Handle Missing Courses from Program Plans
    print("Scanning program plans for missing courses...")
    df_ug = load_csv(CSV_PATHS["program_plans"])
    df_gr = load_csv(CSV_PATHS["graduate_program_plans"])
    df_conc_courses = load_csv(CSV_PATHS["concentration_courses"])
    
    all_codes = set()
    if df_ug is not None: all_codes.update(df_ug['course_code'].unique())
    if df_gr is not None: all_codes.update(df_gr['course_code'].unique())
    if df_conc_courses is not None: all_codes.update(df_conc_courses['course_code'].unique())
    
    cur.execute("SELECT code FROM courses")
    existing_codes = {r[0] for r in cur.fetchall()}
    
    missing_codes = all_codes - existing_codes
    print(f"Found {len(missing_codes)} missing courses. Auto-inserting...")
    
    for code in missing_codes:
        if pd.isna(code): continue
        shortcut = extract_department_shortcut(code)
        dept_id = dept_map.get(shortcut)
        
        # Try to find title from program plans if available
        title = "Unknown Course"
        if df_ug is not None and code in df_ug['course_code'].values:
            title = df_ug[df_ug['course_code'] == code]['course_title'].values[0]
        elif df_gr is not None and code in df_gr['course_code'].values:
            title = df_gr[df_gr['course_code'] == code]['course_title'].values[0]
        
        cur.execute("""
            INSERT INTO courses (code, title, department_id) 
            VALUES (%s, %s, %s) ON CONFLICT (code) DO NOTHING
        """, (code, title, dept_id))
    conn.commit()

    # Re-map course codes to IDs (after including missing ones)
    cur.execute("SELECT code, id FROM courses")
    course_map = dict(cur.fetchall())

    # 4. Concentrations & Junction Table
    print("Loading concentrations...")
    df_conc = load_csv(CSV_PATHS["concentrations"])
    if df_conc is not None:
        for _, row in df_conc.iterrows():
            cur.execute("""
                INSERT INTO concentrations (id, name, description, department_id) 
                VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
            """, (int(row['id']), row['name'], row['description'], int(row['department_id']) if pd.notna(row['department_id']) else None))
            
            # Offered To
            if pd.notna(row['offered_to']):
                shortcuts = [s.strip() for s in str(row['offered_to']).split(',')]
                for s in shortcuts:
                    if s in dept_map:
                        cur.execute("INSERT INTO concentration_departments (concentration_id, department_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (int(row['id']), dept_map[s]))
    conn.commit()

    # 5. Concentration Courses
    print("Loading concentration courses...")
    if df_conc_courses is not None:
        values = []
        for _, row in df_conc_courses.iterrows():
            course_id = course_map.get(row['course_code'])
            values.append((
                int(row['id']),
                int(row['concentration_id']),
                course_id,
                row['course_code'],
                row['course_title'],
                row['description'],
                row['prerequisites'],
                int(row['semester']) if pd.notna(row['semester']) else None
            ))
        extras.execute_values(cur, """
            INSERT INTO concentration_courses (id, concentration_id, course_id, course_code, course_title, description, prerequisites, semester) 
            VALUES %s ON CONFLICT (id) DO NOTHING
        """, values)
    conn.commit()

    # 6. Program Plans (UG)
    print("Loading undergraduate program plans...")
    if df_ug is not None:
        values = []
        for _, row in df_ug.iterrows():
            course_id = course_map.get(row['course_code'])
            values.append((
                int(row['id']),
                int(row['department_id']) if pd.notna(row['department_id']) else None,
                int(row['year_level']) if pd.notna(row['year_level']) else None, # Note: some year_levels might be strings in CSV, but my SQL schema expects INTEGER. If csv has strings like "Freshman", we should map them.
                int(row['semester']) if pd.notna(row['semester']) else None,
                course_id,
                row['course_code'],
                row['course_title'],
                int(row['lecture_hours']) if pd.notna(row['lecture_hours']) else None,
                int(row['lab_hours']) if pd.notna(row['lab_hours']) else None,
                int(row['credits']) if pd.notna(row['credits']) else None,
                row.get('plan_option'),
                'Undergraduate'
            ))
        # Handle string levels if necessary (Freshman=1, Sophomore=2, Junior=3, Senior=4)
        # But looking at CSV, year_level in program_plans_organized.csv is "Freshman" etc.
        # Let's fix the year_level mapping:
        level_map = {"Freshman": 1, "Sophomore": 2, "Junior": 3, "Senior": 4, "S0": 0, "Graduate": 5}
        
        fixed_values = []
        for v in values:
            v_list = list(v)
            if isinstance(v[2], str) and v[2] in level_map:
                v_list[2] = level_map[v[2]]
            elif isinstance(v[2], str):
                v_list[2] = None # Or keep as is if schema allowed string
            
            # Fix semester string "Semester 1" -> 1
            if isinstance(v[3], str) and "Semester" in v[3]:
                try: v_list[3] = int(v[3].split()[-1])
                except: v_list[3] = None
            
            fixed_values.append(tuple(v_list))

        extras.execute_values(cur, """
            INSERT INTO program_plans (id, department_id, year_level, semester, course_id, course_code, course_title, lecture_hours, lab_hours, credits, plan_option, plan_type) 
            VALUES %s ON CONFLICT (id) DO NOTHING
        """, fixed_values)
    conn.commit()

    # 7. Program Plans (GR)
    print("Loading graduate program plans...")
    if df_gr is not None:
        values = []
        for _, row in df_gr.iterrows():
            course_id = course_map.get(row['course_code'])
            # year_level is "Graduate" usually
            level_map = {"Freshman": 1, "Sophomore": 2, "Junior": 3, "Senior": 4, "S0": 0, "Graduate": 5}
            year_val = level_map.get(row['year_level'], 5)
            
            values.append((
                int(row['id']),
                int(row['department_id']) if pd.notna(row['department_id']) else None,
                year_val,
                None, # Grad plans often don't have semesters or have "N/A"
                course_id,
                row['course_code'],
                row['course_title'],
                int(row['lecture_hours']) if pd.notna(row['lecture_hours']) else None,
                int(row['lab_hours']) if pd.notna(row['lab_hours']) else None,
                int(row['credits']) if pd.notna(row['credits']) else None,
                row.get('plan_option'),
                'Graduate'
            ))
        extras.execute_values(cur, """
            INSERT INTO program_plans (id, department_id, year_level, semester, course_id, course_code, course_title, lecture_hours, lab_hours, credits, plan_option, plan_type) 
            VALUES %s ON CONFLICT (id) DO NOTHING
        """, values)
    conn.commit()

    print("Migration completed successfully with auto-repair for missing courses!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nError during migration: {e}")
        print("\nMake sure your PostgreSQL database is running and credentials in DB_CONFIG are correct.")
