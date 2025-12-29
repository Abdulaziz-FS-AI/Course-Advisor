-- Verification Queries for KFUPM Database

SELECT 'Departments' as table_name, COUNT(*) FROM departments
UNION ALL
SELECT 'Courses' as table_name, COUNT(*) FROM courses
UNION ALL
SELECT 'Concentrations' as table_name, COUNT(*) FROM concentrations
UNION ALL
SELECT 'Program Plans' as table_name, COUNT(*) FROM program_plans
UNION ALL
SELECT 'Concentration Courses' as table_name, COUNT(*) FROM concentration_courses;

-- Check for courses without departments
SELECT code, title FROM courses WHERE department_id IS NULL LIMIT 10;

-- Check a specific program plan (e.g. CS - Department 16)
SELECT year_level, semester, course_code, course_title 
FROM program_plans 
WHERE department_id = 16 
ORDER BY year_level, semester;
