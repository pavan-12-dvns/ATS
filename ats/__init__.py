import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# 1️⃣ JOB TEMPLATES TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS job_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    mandatory_skills TEXT,
    min_experience INTEGER,
    required_education TEXT,
    weight_skills INTEGER,
    weight_experience INTEGER,
    weight_education INTEGER
)
""")

# 2️⃣ JOBS TABLE (FINAL SAVED JOBS)
cur.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    mandatory_skills TEXT,
    min_experience INTEGER,
    required_education TEXT,
    weight_skills INTEGER,
    weight_experience INTEGER,
    weight_education INTEGER
)
""")

# 3️⃣ INSERT FAMOUS JOB TEMPLATES (ONLY IF EMPTY)
cur.execute("SELECT COUNT(*) FROM job_templates")
count = cur.fetchone()[0]

if count == 0:
    cur.executemany("""
    INSERT INTO job_templates
    (title, mandatory_skills, min_experience, required_education,
     weight_skills, weight_experience, weight_education)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("Software Engineer", "python,sql,git", 2, "bachelor", 50, 30, 20),
        ("Frontend Developer", "html,css,javascript,react", 1, "bachelor", 60, 25, 15),
        ("Backend Developer", "python,node.js,sql", 2, "bachelor", 60, 25, 15),
        ("Data Analyst", "python,sql,excel", 1, "bachelor", 55, 30, 15),
        ("DevOps Engineer", "linux,docker,kubernetes", 3, "bachelor", 60, 30, 10),
        ("Full Stack Developer", "python,react,sql", 2, "bachelor", 60, 25, 15),
        ("Mobile App Developer", "java,kotlin,android", 1, "bachelor", 55, 30, 15),
        ("Cloud Engineer", "aws,linux,terraform", 2, "bachelor", 60, 30, 10),
        ("QA Engineer", "testing,selenium,python", 1, "bachelor", 50, 30, 20),
        ("AI Engineer", "python,ml,deep learning", 2, "master", 65, 25, 10)
    ])

conn.commit()
conn.close()

print("✅ Database initialized successfully")
