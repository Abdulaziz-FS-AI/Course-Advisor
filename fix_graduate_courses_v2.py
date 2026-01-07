#!/usr/bin/env python3
"""
Enhanced Fix for Graduate Courses Data Import
==============================================
This script fixes the graduate courses and program plans data by:
1. Detecting and fixing swapped course_code/course_title in program_plans
2. Updating courses table with correct credit hours from JSON
3. Updating program_plans table with correct data from the courses table
4. Handling all departments

Author: Claude Code
Date: 2026-01-07
"""

import sqlite3
import json
import re

# File paths
DB_PATH = '/home/shared_dir/vercel_app/api/data/SQL/kfupm_relational.db'
JSON_PATH = '/home/shared_dir/vercel_app/api/data/SQL/processed_graduate_courses.json'

def load_json_courses():
    """Load all graduate courses from JSON file"""
    print("📖 Loading graduate courses from JSON...")
    with open(JSON_PATH, 'r') as f:
        courses = json.load(f)

    courses_dict = {course['code']: course for course in courses}
    print(f"✅ Loaded {len(courses_dict)} graduate courses from JSON\n")
    return courses_dict

def is_course_code(text):
    """Check if text looks like a course code (e.g., 'AE 599', 'CHE 712')"""
    if not text:
        return False
    # Pattern: 2-4 letters, space, 3-4 digits
    pattern = r'^[A-Z]{2,4}\s+\d{3,4}[A-Z]?$'
    return bool(re.match(pattern, text.strip()))

def fix_swapped_code_title(conn):
    """Fix swapped course_code and course_title in program_plans"""
    print("🔄 Fixing swapped course_code and course_title...")
    cursor = conn.cursor()

    # Find entries where course_title looks like a course code
    cursor.execute("""
        SELECT id, course_code, course_title
        FROM program_plans
        WHERE plan_type = 'Graduate'
    """)

    rows = cursor.fetchall()
    swapped_count = 0

    for row in rows:
        plan_id, course_code, course_title = row

        # Check if title looks like a code and code doesn't look like a code
        if course_title and is_course_code(course_title) and not is_course_code(course_code):
            # Swap them!
            cursor.execute("""
                UPDATE program_plans
                SET course_code = ?, course_title = ?
                WHERE id = ?
            """, (course_title, course_code, plan_id))
            swapped_count += 1

    conn.commit()
    print(f"✅ Fixed {swapped_count} swapped entries\n")
    return swapped_count

def update_courses_table(conn, json_courses):
    """Update courses table with correct data from JSON"""
    print("🔧 Updating courses table with correct credit/hour data...")
    cursor = conn.cursor()

    updated_count = 0
    not_found_count = 0

    cursor.execute("""
        SELECT id, code, lecture_hours, lab_hours, credits
        FROM courses
        WHERE type = 'Graduate'
    """)
    db_courses = cursor.fetchall()

    for db_course in db_courses:
        course_id, code, db_lecture, db_lab, db_credits = db_course
        json_course = json_courses.get(code)

        if not json_course:
            not_found_count += 1
            continue

        json_lecture = json_course.get('lecture_hours')
        json_lab = json_course.get('lab_hours')
        json_credits = json_course.get('credits')

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

    conn.commit()
    print(f"✅ Updated {updated_count} courses in courses table\n")

def fix_program_plans_table(conn):
    """Fix program_plans table by updating from courses table"""
    print("🔧 Fixing program_plans table with data from courses table...")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pp.id, pp.course_code, pp.course_id
        FROM program_plans pp
        WHERE pp.plan_type = 'Graduate'
    """)
    program_plans = cursor.fetchall()

    updated_count = 0
    not_found_count = 0
    updated_course_id_count = 0

    for plan in program_plans:
        plan_id, course_code, course_id = plan

        # Try to find the course by code first
        cursor.execute("""
            SELECT id, lecture_hours, lab_hours, credits
            FROM courses
            WHERE code = ? AND type = 'Graduate'
        """, (course_code,))
        course_data = cursor.fetchone()

        if course_data:
            c_id, c_lecture, c_lab, c_credits = course_data

            # Update program plan with correct data
            cursor.execute("""
                UPDATE program_plans
                SET course_id = ?, lecture_hours = ?, lab_hours = ?, credits = ?
                WHERE id = ?
            """, (c_id, c_lecture, c_lab, c_credits, plan_id))
            updated_count += 1

            # Track if we also updated the course_id
            if course_id != c_id:
                updated_course_id_count += 1
        else:
            not_found_count += 1

    conn.commit()
    print(f"✅ Updated {updated_count} program plan entries")
    print(f"ℹ️  Fixed {updated_course_id_count} course_id references")
    if not_found_count > 0:
        print(f"⚠️  {not_found_count} entries could not find matching course (likely electives/placeholders)\n")
    else:
        print()

def verify_fixes(conn):
    """Verify that fixes were applied correctly"""
    print("🔍 Verifying fixes...\n")
    cursor = conn.cursor()

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

    print("="*105)
    print(f"{'Code':<6} {'Department':<40} {'Total':<7} {'✅ Valid':<12} {'❌ Zero':<12} {'Avg Credits':<12}")
    print("="*105)

    total_courses = 0
    total_valid = 0
    total_zero = 0

    for row in results:
        code, name, total, zero, valid, avg = row
        total_courses += total
        total_valid += valid
        total_zero += zero
        avg_str = f"{avg:.1f}" if avg else "N/A"
        status = "✅" if zero == 0 else "⚠️"
        print(f"{code:<6} {name:<40} {total:<7} {valid:<12} {zero:<12} {avg_str:<12} {status}")

    print("="*105)
    print(f"{'TOTAL':<6} {'':<40} {total_courses:<7} {total_valid:<12} {total_zero:<12}")
    print("="*105)

    success_rate = (total_valid / total_courses * 100) if total_courses > 0 else 0
    print(f"\n📊 Success Rate: {success_rate:.1f}% ({total_valid}/{total_courses} entries have valid credits)")

    if total_zero == 0:
        print("✅ SUCCESS! All program plans now have valid credit data!")
    elif total_zero < 200:
        print(f"⚠️  {total_zero} entries still have zero credits (likely electives/placeholders)")
    else:
        print(f"❌ WARNING: {total_zero} program plan entries still have zero credits")

    print()

def show_remaining_issues(conn):
    """Show what entries still have issues"""
    print("🔍 Analyzing remaining zero-credit entries...\n")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT course_code, COUNT(*) as count
        FROM program_plans
        WHERE plan_type = 'Graduate' AND (credits = 0 OR credits IS NULL)
        GROUP BY course_code
        ORDER BY count DESC
        LIMIT 15
    """)

    results = cursor.fetchall()

    if results:
        print("Top 15 remaining zero-credit entries (likely placeholders/electives):")
        print(f"{'Course Code':<40} {'Count':<10}")
        print("="*50)
        for row in results:
            code, count = row
            print(f"{code:<40} {count:<10}")
        print()

def main():
    """Main execution function"""
    print("\n" + "="*105)
    print("🎓 ENHANCED GRADUATE COURSES DATA FIX SCRIPT")
    print("="*105 + "\n")

    json_courses = load_json_courses()

    print("📊 Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    print("✅ Connected\n")

    try:
        # Step 1: Fix swapped course_code and course_title
        fix_swapped_code_title(conn)

        # Step 2: Update courses table
        update_courses_table(conn, json_courses)

        # Step 3: Fix program_plans table
        fix_program_plans_table(conn)

        # Step 4: Verify fixes
        verify_fixes(conn)

        # Step 5: Show remaining issues
        show_remaining_issues(conn)

        print("="*105)
        print("✅ SCRIPT COMPLETED SUCCESSFULLY!")
        print("="*105 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()
        print("📊 Database connection closed\n")

if __name__ == "__main__":
    main()
