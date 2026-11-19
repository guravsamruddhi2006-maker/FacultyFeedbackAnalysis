-- FacultyInsight AI - base master data
-- Master data is inserted once and reused across academic years.
BEGIN;

INSERT INTO departments (name, code)
VALUES ('Computer Science and Engineering', 'CSE')
ON CONFLICT (code) DO NOTHING;

INSERT INTO semesters (semester_number)
VALUES (1),(2),(3),(4),(5),(6),(7),(8)
ON CONFLICT (semester_number) DO NOTHING;

INSERT INTO academic_years (academic_year)
VALUES ('2025-26'), ('2026-27'), ('2027-28'), ('2028-29')
ON CONFLICT (academic_year) DO NOTHING;

INSERT INTO feedback_questions (question_text, is_active)
SELECT q, TRUE
FROM (VALUES
    ('Explains concepts clearly.'),
    ('Has good subject knowledge.'),
    ('Encourages student participation.'),
    ('Uses practical examples.'),
    ('Completes the syllabus.')
) AS seed(q)
WHERE NOT EXISTS (SELECT 1 FROM feedback_questions);

-- Semester 8 is internship-only: no subjects are intentionally seeded for it.
INSERT INTO subjects (subject_code, subject_name, semester_number) VALUES
('1BAIA103/BETC105X', 'Introduction to AI and Applications', 1),
('1BCHEC102', 'Applied Chemistry for CV', 1),
('1BENG106', 'Communication Skills', 1),
('1BESC104X', 'Engineering Science Course-I', 1),
('1BICO107X', 'Indian Constitution & Engineering Ethics', 1),
('1BIDTL158', 'Innovation & Design Thinking (IDEA Lab) (Project Based Learning)', 1),
('1BMATC101', 'Applied Mathematics-I', 1),
('1BPLC105X', 'Programming Language Course', 1),
('1BCEDS203', 'Computer-Aided Engineering Drawing for CSE Stream', 2),
('1BEIT205', 'PSC: Programming in C', 2),
('1BESC204C', 'ESC-II: Introduction to Electronics and Communication Engineering', 2),
('1BKSK209', 'Samskrutika Kannada / Balake Kannada', 2),
('1BMATS201', 'Numerical Methods: CSE Stream', 2),
('1BPHYS202', 'Quantum Physics and Applications (CSE Stream)', 2),
('1BPOPL207', 'Program-Specific Course Lab: C Programming Lab', 2),
('1BPRJ258', 'Interdisciplinary Project-Based Learning (SAAE)', 2),
('1BSK206', 'Soft Skills', 2),
('1BCS301', 'Probability, Distributions and Statistics', 3),
('1BCS302', 'Object Oriented Programming with Java', 3),
('1BCS303', 'Digital Design & Computer Organization', 3),
('1BCS304', 'Operating Systems', 3),
('1BCS305', 'Data Structures and Applications', 3),
('1BCSL306', 'Data Structures Laboratory', 3),
('1BCSL307A', 'Project Management with GIT Lab', 3),
('BBOC407', 'Biology for Computer Engineers', 4),
('BCS401', 'Analysis & Design of Algorithms', 4),
('BCS402', 'Microcontrollers', 4),
('BCS403', 'Database Management Systems', 4),
('BCS405B', 'Graph Theory', 4),
('BCS456B', 'Capacity Planning for IT', 4),
('BCSL404', 'Analysis & Design of Algorithms Lab', 4),
('BUHK408', 'Universal Human Values Course', 4),
('BYOK459', 'Yoga', 4),
('BCS501', 'Software Engineering and Management', 5),
('BCS502', 'Computer Networks', 5),
('BCS503', 'Theory of Computation', 5),
('BCS515A', 'Artificial Intelligence', 5),
('BCSL504', 'Web Technology Lab', 5),
('BCSS586', 'Mini Project', 5),
('BESK508', 'Environmental Studies', 5),
('BRMK557', 'Research Methodology & IPR', 5),
('BCS601', 'Cloud Computing (Open Stack/Google)', 6),
('BCS602', 'Machine Learning', 6),
('BCS613D', 'Advanced Java', 6),
('BCS654A', 'Introduction to Data Structures', 6),
('BCS685', 'Project Phase-1', 6),
('BCSL606', 'Machine Learning Lab', 6),
('BIKS609', 'Indian Knowledge System', 6),
('BSCL657B', 'React Lab', 6),
('BCS701', 'Internet of Things', 7),
('BCS702', 'Parallel Computing', 7),
('BCS703', 'Cryptography & Network Security', 7),
('BCS714X', 'Big Data Analytics', 7),
('BCS755X', 'Open-Elective Course', 7)
ON CONFLICT (subject_code) DO NOTHING;

COMMIT;
