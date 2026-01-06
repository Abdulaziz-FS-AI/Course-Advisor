import sqlite3
import json
import csv
import re
from pathlib import Path

# Config
BASE_DIR = Path("/home/shared_dir/vercel_app")
DB_PATH = BASE_DIR / "api/data/SQL/kfupm_relational.db"
JSON_PATH = Path("/home/shared_dir/data/processed_graduate_courses.json")
CSV_PATH = Path("/home/shared_dir/data/SQL/graduate_program_plans.csv")

def main():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Load Department Mapping
    print("Loading departments...")
    cursor.execute("SELECT id, shortcut FROM departments")
    dept_map = {row["shortcut"]: row["id"] for row in cursor.fetchall()}
    print(f"Loaded {len(dept_map)} departments.")

    # 2. Import Graduate Courses from JSON
    print(f"Loading graduate courses from {JSON_PATH}...")
    with open(JSON_PATH, "r") as f:
        courses = json.load(f)
    
    courses_added = 0
    courses_skipped = 0
    
    for course in courses:
        code = course.get("code", "").strip()
        if not code:
            continue
            
        # Extract dept prefix (e.g. "SWE" from "SWE 501")
        match = re.match(r"^([A-Z]+)\s", code)
        if not match:
            print(f"Skipping course with invalid code format: {code}")
            courses_skipped += 1
            continue
            
        prefix = match.group(1)
        dept_id = dept_map.get(prefix)
        
        if not dept_id:
            print(f"Warning: No department found for prefix {prefix} (Course: {code})")
            courses_skipped += 1
            continue
            
        try:
            cursor.execute("""
                INSERT INTO courses (
                    code, title, lecture_hours, lab_hours, credits, 
                    department_id, type, description, prerequisites
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    description = excluded.description,
                    prerequisites = excluded.prerequisites,
                    type = 'Graduate'
            """, (
                code,
                course.get("title", ""),
                course.get("lecture_hours", 0),
                course.get("lab_hours", 0),
                course.get("credits", 0),
                dept_id,
                "Graduate",
                course.get("description", ""),
                course.get("prerequisites", "")
            ))
            courses_added += 1
        except sqlite3.Error as e:
            print(f"Error inserting course {code}: {e}")
            courses_skipped += 1

    print(f"Courses Import: {courses_added} added/updated, {courses_skipped} skipped.")

    # 3. Import Graduate Program Plans from CSV
    print(f"Loading program plans from {CSV_PATH}...")
    plans_added = 0
    plans_skipped = 0
    
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            course_code = row.get("course_code", "").strip()
            
            # Find course ID
            cursor.execute("SELECT id FROM courses WHERE code = ?", (course_code,))
            res = cursor.fetchone()
            course_id = res["id"] if res else None
            
            try:
                cursor.execute("""
                    INSERT INTO program_plans (
                        department_id, year_level, semester, course_id, 
                        course_code, course_title, lecture_hours, lab_hours, 
                        credits, plan_option, plan_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("department_id"),
                    "Graduate",  # Explicitly set as Graduate year_level
                    row.get("semester", "N/A"),
                    course_id,
                    course_code,
                    row.get("course_title", ""),
                    row.get("lecture_hours", 0),
                    row.get("lab_hours", 0),
                    row.get("credits", 0),
                    row.get("plan_option", ""),
                    "Graduate"   # Explicitly set as Graduate plan_type
                ))
                plans_added += 1
            except sqlite3.Error as e:
                print(f"Error inserting plan for {course_code}: {e}")
                plans_skipped += 1

    print(f"Plans Import: {plans_added} added, {plans_skipped} skipped.")

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
