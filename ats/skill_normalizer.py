"""
Canonical skill normalization for ATS.
All skills are stored and compared as lowercase, trimmed strings.
Aliases map common variants to one canonical form.
"""

SKILL_ALIASES = {
    # Backend
    "python":           ["py", "python3", "python2"],
    "java":             ["java8", "java11", "java17", "java se", "java ee"],
    "node.js":          ["node", "nodejs", "node js"],
    "c#":               ["csharp", "c sharp", "dotnet", ".net"],
    "go":               ["golang"],
    "ruby":             ["ruby on rails", "ror"],
    "php":              ["php7", "php8"],
    "swift":            [],
    "kotlin":           [],
    "rust":             [],
    "typescript":       ["ts"],
    "c++":              ["cpp", "c plus plus"],
    "scala":            [],
    # Frontend
    "react":            ["reactjs", "react.js", "react js"],
    "angular":          ["angularjs", "angular.js", "angular js"],
    "vue":              ["vuejs", "vue.js", "vue js"],
    "javascript":       ["js", "ecmascript", "es6", "es2015", "es2016", "es2017", "es2020", "vanilla js"],
    "html":             ["html5"],
    "css":              ["css3"],
    "sass":             ["scss"],
    "next.js":          ["nextjs", "next js"],
    "svelte":           [],
    "tailwind":         ["tailwindcss", "tailwind css"],
    "bootstrap":        [],
    # Frameworks
    "flask":            [],
    "django":           [],
    "spring":           ["spring boot", "spring framework", "springboot"],
    "express":          ["expressjs", "express.js"],
    "fastapi":          [],
    "laravel":          [],
    "asp.net":          ["aspnet", "asp net"],
    # Databases
    "mysql":            ["mariadb"],
    "postgresql":       ["postgres", "psql", "pg", "postgre"],
    "sqlite":           [],
    "mongodb":          ["mongo"],
    "redis":            [],
    "elasticsearch":    ["elastic"],
    "cassandra":        [],
    "dynamodb":         ["dynamo db"],
    "sql":              ["t-sql", "plsql", "pl/sql", "ansi sql"],
    "oracle":           ["oracle db", "oracle database"],
    "mssql":            ["sql server", "microsoft sql server"],
    # Cloud
    "aws":              ["amazon web services", "amazon aws"],
    "azure":            ["microsoft azure"],
    "gcp":              ["google cloud", "google cloud platform"],
    # DevOps
    "docker":           ["docker container", "containerization"],
    "kubernetes":       ["k8s"],
    "ci/cd":            ["cicd", "continuous integration", "continuous delivery", "ci cd"],
    "terraform":        [],
    "ansible":          [],
    "helm":             [],
    "linux":            ["unix", "shell scripting"],
    "jenkins":          [],
    # Architecture
    "system design":    ["systems design"],
    "microservices":    ["microservice", "micro services"],
    "rest":             ["rest api", "restful", "rest apis", "restful api"],
    "graphql":          [],
    "grpc":             [],
    # Data / ML
    "machine learning": ["ml", "machine-learning"],
    "deep learning":    ["dl", "deep-learning", "neural networks", "neural network"],
    "data science":     ["data analysis", "data analytics"],
    "numpy":            [],
    "pandas":           [],
    "tensorflow":       [],
    "pytorch":          [],
    "scikit-learn":     ["sklearn"],
    # Testing
    "selenium":         [],
    "jest":             [],
    "pytest":           [],
    "junit":            [],
    # Other
    "git":              ["github", "gitlab", "version control", "bitbucket"],
    "agile":            ["scrum", "kanban"],
    "excel":            ["microsoft excel", "ms excel"],
    "bash":             ["shell"],
}

# Build reverse map: alias -> canonical
_ALIAS_MAP: dict = {}
for canonical, aliases in SKILL_ALIASES.items():
    _ALIAS_MAP[canonical.lower().strip()] = canonical.lower().strip()
    for alias in aliases:
        _ALIAS_MAP[alias.lower().strip()] = canonical.lower().strip()


def normalize_skill(skill: str) -> str:
    """Normalize a single skill string to its canonical lowercase form."""
    if not skill:
        return ""
    s = skill.lower().strip()
    return _ALIAS_MAP.get(s, s)


def normalize_skill_list(skills: list) -> list:
    """Normalize a list of skills; deduplicates after normalization."""
    seen = set()
    result = []
    for skill in skills:
        if not skill:
            continue
        n = normalize_skill(skill)
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result
