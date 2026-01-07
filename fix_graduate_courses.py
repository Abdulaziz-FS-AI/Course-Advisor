#!/usr/bin/env python3
"""
Fix Graduate Courses Data Import
=================================
This script fixes the graduate courses and program plans data by:
1. Updating courses table with correct credit hours, lecture hours, and lab hours from JSON
2. Updating program_plans table with correct data from the courses table
3. Handling all departments, not just one

Author: Claude Code
Date: 2026-01-07
"""

import sqlite3
import json
from collections import defaultdict

# File paths
DB_PATH = '/home/shared_dir/vercel_app/api/data/SQL/kfupm_relational.db'
JSON_PATH = '/home/shared_dir/vercel_app/api/data/SQL/processed_graduate_courses.json'

def load_json_courses():
    """Load all graduate courses from JSON file"""
    print("📖 Loading graduate courses from JSON...")
    with open(JSON_PATH, 'r') as f:
        courses = json.load(f)

    # Group by course code for easy lookup
    courses_dict = {course['code']: course for course in courses}
    print(f"✅ Loaded {len(courses_dict)} graduate courses from JSON\n")
    return courses_dict

def get_department_mappings(conn):
    """Get department code to ID mappings"""
    print("🗺️  Creating department mappings...")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, shortcut FROM departments")
    departments = cursor.fetchall()

    dept_map = {dept[2]: dept[0] for dept in departments if dept[2]}  # shortcut -> id
    print(f"✅ Mapped {len(dept_map)} departments\n")
    return dept_map

def update_courses_table(conn, json_courses):
    """Update courses table with correct data from JSON"""
    print("🔧 Updating courses table with correct credit/hour data...")
    cursor = conn.cursor()

    updated_count = 0
    not_found_count = 0
    already_correct = 0

    # Get all graduate courses from database
    cursor.execute("""
        SELECT id, code, lecture_hours, lab_hours, credits
        FROM courses
        WHERE type = 'Graduate'
    """)
    db_courses = cursor.fetchall()

    for db_course in db_courses:
        course_id, code, db_lecture, db_lab, db_credits = db_course

        # Find matching course in JSON
        json_course = json_courses.get(code)

        if not json_course:
            not_found_count += 1
            continue

        json_lecture = json_course.get('lecture_hours')
        json_lab = json_course.get('lab_hours')
        json_credits = json_course.get('credits')

        # Check if update is needed
        needs_update = (
            (db_lecture != json_lecture and json_lecture is not None) or
            (db_lab != json_lab and json_lab is not None) or
            (db_credits != json_credits and json_credits is not None)
        )

        if needs_update:
            cursor.execute("""
                UPDATE courses
                SET lecture_hours = ?, lab_hours = ?, credits = ?
                WHERE id = ?
            """, (json_lecture, json_lab, json_credits, course_id))
            updated_count += 1
        else:
            already_correct += 1

    conn.commit()
    print(f"✅ Updated {updated_count} courses")
    print(f"ℹ️  {already_correct} courses already had correct data")
    if not_found_count > 0:
        print(f"⚠️  {not_found_count} courses not found in JSON\n")
    else:
        print()

def fix_program_plans_table(conn):
    """Fix program_plans table by updating from courses table"""
    print("🔧 Fixing program_plans table with data from courses table...")
    cursor = conn.cursor()

    # Get all program plans
    cursor.execute("""
        SELECT pp.id, pp.course_code, pp.course_id, pp.lecture_hours, pp.lab_hours, pp.credits
        FROM program_plans pp
        WHERE pp.plan_type = 'Graduate'
    """)
    program_plans = cursor.fetchall()

    updated_count = 0
    not_found_count = 0
    already_correct = 0

    for plan in program_plans:
        plan_id, course_code, course_id, pp_lecture, pp_lab, pp_credits = plan

        # Try to find the course by course_id first, then by course_code
        course_data = None

        if course_id:
            cursor.execute("""
                SELECT lecture_hours, lab_hours, credits
                FROM courses
                WHERE id = ?
            """, (course_id,))
            course_data = cursor.fetchone()

        # If not found by ID, try by code
        if not course_data and course_code:
            cursor.execute("""
                SELECT lecture_hours, lab_hours, credits
                FROM courses
                WHERE code = ? AND type = 'Graduate'
            """, (course_code,))
            course_data = cursor.fetchone()

        if course_data:
            c_lecture, c_lab, c_credits = course_data

            # Check if update is needed (handle None values)
            needs_update = (
                (pp_lecture != c_lecture and c_lecture is not None) or
                (pp_lab != c_lab and c_lab is not None) or
                (pp_credits != c_credits and c_credits is not None)
            )

            if needs_update:
                cursor.execute("""
                    UPDATE program_plans
                    SET lecture_hours = ?, lab_hours = ?, credits = ?
                    WHERE id = ?
                """, (c_lecture, c_lab, c_credits, plan_id))
                updated_count += 1
            else:
                already_correct += 1
        else:
            not_found_count += 1

    conn.commit()
    print(f"✅ Updated {updated_count} program plan entries")
    print(f"ℹ️  {already_correct} entries already had correct data")
    if not_found_count > 0:
        print(f"⚠️  {not_found_count} entries could not find matching course\n")
    else:
        print()

def verify_fixes(conn):
    """Verify that fixes were applied correctly"""
    print("🔍 Verifying fixes...\n")
    cursor = conn.cursor()

    # Check program_plans by department
    cursor.execute("""
        SELECT
            d.shortcut,
            d.name,
            COUNT(pp.id) as total_courses,
            SUM(CASE WHEN pp.credits = 0 OR pp.credits IS NULL THEN 1 ELSE 0 END) as zero_credit_courses,
            SUM(CASE WHEN pp.credits > 0 THEN 1 ELSE 0 END) as valid_credit_courses,
            AVG(CASE WHEN pp.credits > 0 THEN pp.credits ELSE NULL END) as avg_credits
        FROM departments d
        LEFT JOIN program_plans pp ON d.id = pp.department_id AND pp.plan_type = 'Graduate'
        GROUP BY d.id, d.name, d.shortcut
        HAVING COUNT(pp.id) > 0
        ORDER BY d.shortcut
    """)

    results = cursor.fetchall()

    print("="*100)
    print(f"{'Code':<6} {'Department':<40} {'Total':<7} {'✅ Valid':<10} {'❌ Zero':<10} {'Avg Credits':<12}")
    print("="*100)

    total_courses = 0
    total_valid = 0
    total_zero = 0

    for row in results:
        code, name, total, zero, valid, avg = row
        total_courses += total
        total_valid += valid
        total_zero += zero
        avg_str = f"{avg:.1f}" if avg else "N/A"
        print(f"{code:<6} {name:<40} {total:<7} {valid:<10} {zero:<10} {avg_str:<12}")

    print("="*100)
    print(f"{'TOTAL':<6} {'':<40} {total_courses:<7} {total_valid:<10} {total_zero:<10}")
    print("="*100)

    if total_zero == 0:
        print("\n✅ SUCCESS! All program plans now have valid credit data!")
    else:
        print(f"\n⚠️  WARNING: {total_zero} program plan entries still have zero credits")

    print()

def main():
    """Main execution function"""
    print("\n" + "="*100)
    print("🎓 GRADUATE COURSES DATA FIX SCRIPT")
    print("="*100 + "\n")

    # Load JSON data
    json_courses = load_json_courses()

    # Connect to database
    print("📊 Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    print("✅ Connected\n")

    try:
        # Get department mappings
        dept_map = get_department_mappings(conn)

        # Step 1: Update courses table
        update_courses_table(conn, json_courses)

        # Step 2: Fix program_plans table
        fix_program_plans_table(conn)

        # Step 3: Verify fixes
        verify_fixes(conn)

        print("="*100)
        print("✅ SCRIPT COMPLETED SUCCESSFULLY!")
        print("="*100 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("📊 Database connection closed\n")

if __name__ == "__main__":
    main()
