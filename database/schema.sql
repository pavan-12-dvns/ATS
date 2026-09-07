-- ATS Database Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('hr', 'candidate')),
    company TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    mandatory_skills TEXT NOT NULL,
    optional_skills TEXT,
    min_experience INTEGER DEFAULT 0,
    required_education TEXT,
    skill_weight INTEGER NOT NULL,
    experience_weight INTEGER NOT NULL,
    education_weight INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    is_closed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    CHECK(skill_weight + experience_weight + education_weight = 100)
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    resume_path TEXT NOT NULL,
    resume_hash TEXT NOT NULL,
    parsed_name TEXT,
    parsed_email TEXT,
    parsed_phone TEXT,
    parsed_skills TEXT,
    parsed_experience INTEGER DEFAULT 0,
    parsed_education TEXT,
    skill_score REAL DEFAULT 0,
    experience_score REAL DEFAULT 0,
    education_score REAL DEFAULT 0,
    weighted_total REAL DEFAULT 0,
    rank_position INTEGER,
    status TEXT DEFAULT 'Under Review' CHECK(status IN ('Under Review', 'Shortlisted', 'Rejected', 'Interview')),
    rejection_reason TEXT,
    matched_skills TEXT,
    missing_skills TEXT,
    partial_matches TEXT,
    score_explanation TEXT,
    feedback TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES users(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    UNIQUE(candidate_id, job_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_applications_job ON applications(job_id);
CREATE INDEX idx_applications_candidate ON applications(candidate_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_audit_user ON audit_log(user_id);

-- =========================
-- JOB TEMPLATES (PREDEFINED)
-- =========================
CREATE TABLE IF NOT EXISTS job_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    mandatory_skills TEXT NOT NULL,
    min_experience INTEGER NOT NULL,
    required_education TEXT NOT NULL,
    weight_skills INTEGER NOT NULL,
    weight_experience INTEGER NOT NULL,
    weight_education INTEGER NOT NULL
);

INSERT INTO job_templates
(title, mandatory_skills, min_experience, required_education, weight_skills, weight_experience, weight_education)
VALUES
('Software Engineer',     'python,sql,git',                   2, 'bachelor', 50, 30, 20),
('Frontend Developer',    'html,css,javascript,react',        1, 'bachelor', 60, 25, 15),
('Backend Developer',     'python,node.js,sql',               2, 'bachelor', 60, 25, 15),
('Data Analyst',          'python,sql,excel',                 1, 'bachelor', 55, 30, 15),
('DevOps Engineer',       'linux,docker,kubernetes',          3, 'bachelor', 60, 30, 10),
('Full Stack Developer',  'javascript,react,node.js,sql',     2, 'bachelor', 60, 25, 15),
('QA Engineer',           'selenium,python',                  1, 'bachelor', 50, 30, 20),
('Data Scientist',        'python,machine learning,sql',      3, 'master',   65, 25, 10),
('Mobile App Developer',  'java,kotlin',                      2, 'bachelor', 60, 25, 15),
('Cloud Engineer',        'aws,linux,terraform',              3, 'bachelor', 60, 30, 10);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT OR IGNORE INTO skills (name) VALUES
-- Backend
('python'), ('java'), ('node.js'), ('c#'), ('go'), ('ruby'), ('php'), ('swift'), ('kotlin'),
('rust'), ('typescript'), ('c++'), ('scala'),
-- Frontend
('react'), ('angular'), ('vue'), ('javascript'), ('html'), ('css'), ('sass'), ('next.js'),
('svelte'), ('tailwind'), ('bootstrap'),
-- Frameworks
('flask'), ('django'), ('spring'), ('express'), ('fastapi'), ('laravel'), ('asp.net'),
-- Databases
('mysql'), ('postgresql'), ('sqlite'), ('mongodb'), ('redis'), ('elasticsearch'),
('cassandra'), ('dynamodb'), ('sql'), ('oracle'), ('mssql'),
-- Cloud
('aws'), ('azure'), ('gcp'),
-- DevOps
('docker'), ('kubernetes'), ('ci/cd'), ('terraform'), ('ansible'), ('helm'), ('linux'), ('jenkins'),
-- Architecture
('system design'), ('microservices'), ('rest'), ('graphql'), ('grpc'),
-- Data / ML
('machine learning'), ('deep learning'), ('data science'), ('numpy'), ('pandas'),
('tensorflow'), ('pytorch'), ('scikit-learn'),
-- Testing
('selenium'), ('jest'), ('pytest'), ('junit'),
-- Other
('git'), ('agile'), ('excel'), ('bash');
