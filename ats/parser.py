import re
import PyPDF2
import docx
from datetime import datetime
from ats.skill_normalizer import normalize_skill, normalize_skill_list

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[ERROR] PDF extraction failed: {e}")
        return ""

def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"[ERROR] DOCX extraction failed: {e}")
        return ""

# Comprehensive skill list matching the normalizer catalog
SKILL_SEARCH_LIST = [
    # Backend
    'python', 'java', 'node.js', 'nodejs', 'c#', 'csharp', 'go', 'golang',
    'ruby', 'php', 'swift', 'kotlin', 'rust', 'typescript', 'c++', 'cpp', 'scala',
    # Frontend
    'react', 'reactjs', 'angular', 'angularjs', 'vue', 'vuejs', 'javascript', 'js',
    'html', 'html5', 'css', 'css3', 'sass', 'scss', 'next.js', 'nextjs',
    'svelte', 'tailwind', 'bootstrap',
    # Frameworks
    'flask', 'django', 'spring', 'express', 'fastapi', 'laravel', 'asp.net',
    # Databases
    'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'mongo', 'redis',
    'elasticsearch', 'cassandra', 'dynamodb', 'sql', 'oracle', 'mssql',
    # Cloud
    'aws', 'azure', 'gcp',
    # DevOps
    'docker', 'kubernetes', 'k8s', 'ci/cd', 'cicd', 'terraform', 'ansible',
    'helm', 'linux', 'unix', 'jenkins', 'bash',
    # Architecture
    'microservices', 'rest', 'restful', 'graphql', 'grpc', 'system design',
    # Data / ML
    'machine learning', 'deep learning', 'data science', 'numpy', 'pandas',
    'tensorflow', 'pytorch', 'scikit-learn', 'sklearn',
    # Testing
    'selenium', 'jest', 'pytest', 'junit',
    # Other
    'git', 'github', 'gitlab', 'agile', 'scrum', 'excel',
]

def parse_resume(filepath, filename):
    if filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(filepath)
    elif filename.lower().endswith('.docx'):
        text = extract_text_from_docx(filepath)
    else:
        return None

    if not text:
        print(f"[ATS_DEBUG] No text extracted from {filename}")
        return None

    print(f"[ATS_DEBUG] Extracted text length: {len(text)} characters")

    text_lower = text.lower()

    # Name: first non-empty line
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    name = lines[0] if lines else filename.replace('.pdf', '').replace('.docx', '')

    # Email
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_lower)
    email = email.group(0) if email else 'Not found'

    # Phone
    phone = re.search(r'(\+?\d{1,3}[-.\\s]?)?\(?\d{3}\)?[-.\\s]?\d{3}[-.\\s]?\d{4}', text)
    phone = phone.group(0) if phone else 'Not found'

    # Skill extraction with frequency counting
    skill_counts_raw = {}
    for skill in SKILL_SEARCH_LIST:
        # Use word boundary matching to avoid false positives (e.g. 'r' matching everywhere)
        if len(skill) <= 2:
            pattern = r'\b' + re.escape(skill) + r'\b'
            count = len(re.findall(pattern, text_lower))
        else:
            count = text_lower.count(skill)
        if count > 0:
            skill_counts_raw[skill] = min(count, 3)

    raw_found_skills = list(skill_counts_raw.keys())
    normalized_skills = normalize_skill_list(raw_found_skills)

    # Build normalized skill_counts
    skill_counts = {}
    for raw_skill in raw_found_skills:
        normalized = normalize_skill(raw_skill)
        count = skill_counts_raw[raw_skill]
        skill_counts[normalized] = skill_counts.get(normalized, 0) + count

    skills = list(set(normalized_skills))

    # Experience years
    experience = 0

    # Pattern 1: "X years of experience" or "X+ years"
    exp_match = re.search(r'(\d+)\s*(?:\+)?\s*years?\s*(?:of)?\s*(?:experience|exp)', text_lower)
    if exp_match:
        experience = int(exp_match.group(1))

    # Pattern 2: Count job date ranges
    job_periods = re.findall(r'(\d{4})\s*[-–]\s*(?:(\d{4})|present|current)', text_lower, re.IGNORECASE)
    if job_periods:
        total_years = 0
        current_year = datetime.now().year
        for start, end in job_periods:
            start_year = int(start)
            end_year = int(end) if end else current_year
            total_years += max(0, end_year - start_year)
        experience = max(experience, total_years)

    # Education
    edu_map = {
        'PhD':        r'ph\.?d|doctorate|doctor\s+of\s+philosophy',
        'Master':     r"master(?:'?s)?|m\.?\s?s\.?|m\.?\s?a\.?|mba|m\.?tech",
        'Bachelor':   r"bachelor(?:'?s)?|b\.?\s?s\.?|b\.?\s?a\.?|b\.?tech|b\.?e\.?|undergraduate\s+degree",
        'Associate':  r"associate(?:'?s)?|a\.?\s?s\.?|a\.?\s?a\.\?",
        'High School':r'high\s+school|secondary\s+school|diploma|12th\s+(?:grade|standard)',
    }

    education = [deg for deg, pat in edu_map.items() if re.search(pat, text_lower)]
    priority = ['PhD', 'Master', 'Bachelor', 'Associate', 'High School']
    education = [e for e in priority if e in education]
    if not education:
        education = ['Not specified']
    else:
        education = education[:1]

    result = {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'skill_counts': skill_counts,
        'experience_years': experience,
        'education': education,
    }

    print(f"[ATS_DEBUG] Parsed result: skills={len(skills)}, exp={experience}, edu={education}")

    return result
