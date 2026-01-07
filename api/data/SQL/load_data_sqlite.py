import pandas as pd
import sqlite3
import os
import re
import csv
import json

# --- Configuration ---
DB_FILE = "/home/shared_dir/vercel_app/api/data/SQL/kfupm_relational.db"

CSV_PATHS = {
    "departments": "/home/shared_dir/vercel_app/api/data/SQL/departments.csv",
    "concentrations": "/home/shared_dir/vercel_app/api/data/SQL/concentrations.csv",
    "concentration_courses": "/home/shared_dir/vercel_app/api/data/SQL/concentration_courses.csv",
    "program_plans": "/home/shared_dir/vercel_app/api/data/SQL/program_plans_organized.csv",
    "graduate_program_plans": "/home/shared_dir/vercel_app/api/data/SQL/graduate_program_plans.csv"
}

JSON_PATHS = {
    "undergraduate_courses": "/home/shared_dir/vercel_app/api/data/SQL/processed_undergraduate_courses.json",
    "graduate_courses": "/home/shared_dir/vercel_app/api/data/SQL/processed_graduate_courses.json"
}

def load_csv_robust(path, expected_cols, headers=None):
    if not os.path.exists(path): return None
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Handle the weird case where header and first row are merged
        if "program_plans_organized.csv" in path:
            # Manually split header
            header = ["id", "department_id", "year_level", "semester", "course_code", "course_title", "lecture_hours", "lab_hours", "credits", "plan_option"]
            # Remaining content: the merge happens at "plan_option1,6,..." -> should be "plan_option\n1,6,..."
            content = content.replace("plan_option1,6,", "plan_option\n1,6,")
            f_seek = content.splitlines()
            reader = csv.reader(f_seek)
            next(reader) # skip header
        else:
            reader = csv.reader(content.splitlines())
            header = next(reader)
        
        for row in reader:
            if len(row) > expected_cols:
                if "concentration_courses" in path:
                    new_row = row[:4] + [", ".join(row[4:-2])] + row[-2:]
                    data.append(new_row)
                else: data.append(row[:expected_cols])
            elif len(row) < expected_cols:
                row.extend([None] * (expected_cols - len(row)))
                data.append(row)
            else: data.append(row)
    return pd.DataFrame(data, columns=header[:expected_cols])

def extract_shortcut(code):
    m = re.match(r'^([A-Z]+)', str(code))
    return m.group(1) if m else None

def migrate():
    print("Initializing...")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")

    print("Creating tables...")
    cur.executescript("""
    DROP TABLE IF EXISTS program_plans; DROP TABLE IF EXISTS concentration_courses; DROP TABLE IF EXISTS concentration_departments;
    DROP TABLE IF EXISTS concentrations; DROP TABLE IF EXISTS courses; DROP TABLE IF EXISTS departments;
    CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT, shortcut TEXT UNIQUE, college TEXT, other_info TEXT, link TEXT);
    CREATE TABLE courses (id INTEGER PRIMARY KEY, code TEXT UNIQUE, title TEXT, lecture_hours INTEGER, lab_hours INTEGER, credits INTEGER, department_id INTEGER, type TEXT, description TEXT, prerequisites TEXT);
    CREATE TABLE concentrations (id INTEGER PRIMARY KEY, name TEXT, description TEXT, department_id INTEGER);
    CREATE TABLE concentration_departments (concentration_id INTEGER, department_id INTEGER, PRIMARY KEY (concentration_id, department_id));
    CREATE TABLE program_plans (id INTEGER PRIMARY KEY, department_id INTEGER, year_level INTEGER, semester INTEGER, course_id INTEGER, course_code TEXT, course_title TEXT, lecture_hours INTEGER, lab_hours INTEGER, credits INTEGER, plan_option TEXT, plan_type TEXT);
    CREATE TABLE concentration_courses (id INTEGER PRIMARY KEY, concentration_id INTEGER, course_id INTEGER, course_code TEXT, course_title TEXT, description TEXT, prerequisites TEXT, semester INTEGER);
    """)

    print("Loading Departments...")
    df = load_csv_robust(CSV_PATHS["departments"], 6)
    if df is not None: df.to_sql('departments', conn, if_exists='append', index=False)
    cur.execute("SELECT shortcut, id FROM departments"); dept_map = dict(cur.fetchall())

    print("Loading Courses from JSON...")
    all_courses_data = []
    if os.path.exists(JSON_PATHS["undergraduate_courses"]):
        with open(JSON_PATHS["undergraduate_courses"], 'r') as f:
            all_courses_data.extend([{"type": "Undergraduate", **c} for c in json.load(f)])
    if os.path.exists(JSON_PATHS["graduate_courses"]):
        with open(JSON_PATHS["graduate_courses"], 'r') as f:
            all_courses_data.extend([{"type": "Graduate", **c} for c in json.load(f)])
            
    if all_courses_data:
        values = []
        for i, course in enumerate(all_courses_data, 1):
            code = course.get('code')
            shortcut = extract_shortcut(code)
            dept_id = dept_map.get(shortcut)
            values.append((
                i, code, course.get('title'), course.get('lecture_hours'), 
                course.get('lab_hours'), course.get('credits'), dept_id, 
                course.get('type'), course.get('description'), course.get('prerequisites')
            ))
        cur.executemany("""
            INSERT INTO courses (id, code, title, lecture_hours, lab_hours, credits, department_id, type, description, prerequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

    print("Auto-repairing missing data...")
    codes = set()
    df_ug = load_csv_robust(CSV_PATHS["program_plans"], 10)
    df_gr = load_csv_robust(CSV_PATHS["graduate_program_plans"], 10)
    df_cc = load_csv_robust(CSV_PATHS["concentration_courses"], 7)
    if df_ug is not None: codes.update(df_ug['course_code'].unique())
    if df_gr is not None: codes.update(df_gr['course_code'].unique())
    if df_cc is not None: codes.update(df_cc['course_code'].unique())
    cur.execute("SELECT code FROM courses"); existing = {r[0] for r in cur.fetchall()}
    for c in (codes - existing): 
        if pd.notna(c): cur.execute("INSERT OR IGNORE INTO courses (code, title, department_id) VALUES (?, ?, ?)", (c, "Legacy/External Course", dept_map.get(extract_shortcut(c))))
    
    cur.execute("SELECT code, id FROM courses"); course_map = dict(cur.fetchall())

    print("Loading Concentrations...")
    df = load_csv_robust(CSV_PATHS["concentrations"], 5)
    if df is not None:
        for _, r in df.iterrows():
            did = int(r['department_id']) if pd.notna(r['department_id']) and int(r['department_id']) in dept_map.values() else None
            cur.execute("INSERT OR IGNORE INTO concentrations (id, name, description, department_id) VALUES (?, ?, ?, ?)", (int(r['id']), r['name'], r['description'], did))
            if pd.notna(r['offered_to']):
                for s in str(r['offered_to']).split(','):
                    if s.strip() in dept_map: cur.execute("INSERT OR IGNORE INTO concentration_departments (concentration_id, department_id) VALUES (?, ?)", (int(r['id']), dept_map[s.strip()]))

    print("Loading concentration_courses...")
    if df_cc is not None:
        for _, r in df_cc.iterrows():
            cur.execute("INSERT OR IGNORE INTO concentration_courses (id, concentration_id, course_id, course_code, course_title, description, prerequisites, semester) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (int(r['id']), int(r['concentration_id']), course_map.get(r['course_code']), r['course_code'], r['course_title'], r['description'], r['prerequisites'], r['semester']))

    print("Loading Program Plans...")
    lmap = {"Freshman": 1, "Sophomore": 2, "Junior": 3, "Senior": 4, "S0": 0}
    for df, ptype in [(df_ug, 'Undergraduate'), (df_gr, 'Graduate')]:
        if df is not None:
            for _, r in df.iterrows():
                sem = None
                if isinstance(r.get('semester'), str) and "Semester" in r['semester']:
                    try: sem = int(r['semester'].split()[-1])
                    except: pass
                yl = lmap.get(r['year_level'], 5)
                cur.execute("INSERT OR IGNORE INTO program_plans (id, department_id, year_level, semester, course_id, course_code, course_title, lecture_hours, lab_hours, credits, plan_option, plan_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (int(r['id']), int(r['department_id']) if pd.notna(r['department_id']) else None, yl, sem, course_map.get(r['course_code']), r['course_code'], r['course_title'], r['lecture_hours'], r['lab_hours'], r['credits'], str(r.get('plan_option', '')), ptype))

    conn.commit()
    print("SUCCESS: Relational database 'kfupm_relational.db' is ready.")
    conn.close()

if __name__ == "__main__":
    migrate()
