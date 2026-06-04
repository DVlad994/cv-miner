import re

# разные написания одного навыка -> канон, чтобы синонимы не считались разными
SKILL_SYNONYMS = {
    # Языки
    "py": "Python", "python3": "Python", "питон": "Python",
    "golang": "Go", "go-lang": "Go",
    "js": "JavaScript", "javascript": "JavaScript", "ecmascript": "JavaScript",
    "ts": "TypeScript",
    "c sharp": "C#", "csharp": "C#", "c#": "C#",
    "c plus plus": "C++", "cpp": "C++", "c++": "C++",
    # Backend / фреймворки
    "fast api": "FastAPI", "fastapi": "FastAPI",
    "drf": "Django", "django rest framework": "Django",
    # Базы данных
    "postgres": "PostgreSQL", "postgre": "PostgreSQL", "psql": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",
    "clickhouse": "ClickHouse", "click house": "ClickHouse",
    # DevOps / инфраструктура
    "k8s": "Kubernetes", "kuber": "Kubernetes", "kubernetes": "Kubernetes",
    "docker": "Docker", "докер": "Docker",
    "ci/cd": "CI/CD", "cicd": "CI/CD", "ci cd": "CI/CD",
    "gitlab ci": "GitLab CI", "github actions": "GitHub Actions",
    "argo cd": "ArgoCD", "argocd": "ArgoCD",
    "prometheus": "Prometheus", "grafana": "Grafana", "helm": "Helm",
    # Очереди / стриминг
    "rabbit": "RabbitMQ", "rabbitmq": "RabbitMQ", "rabbit mq": "RabbitMQ",
    "kafka": "Kafka", "apache kafka": "Kafka",
    # ML
    "torch": "PyTorch", "pytorch": "PyTorch",
    "tf": "TensorFlow", "tensorflow": "TensorFlow",
    "sklearn": "scikit-learn", "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
}

#  нужно, чтобы родственные технологии частично зачитывались
# (требуется Redis, у кандидата Kafka- оба Data, дадим частичный зачёт),
# аналогично Docker, Prometheus, Grafana применяются вместе, хоть и не имеют общего назначения
SKILL_GROUPS = {
    "Backend": {
        "Python", "Go", "Java", "C#", "PHP", "Ruby", "Node.js",
        "Django", "FastAPI", "Flask", "Spring", "REST API", "GraphQL",
    },
    "Frontend": {
        "JavaScript", "TypeScript", "React", "Angular", "Vue",
        "HTML5", "CSS3",
    },
    "DevOps": {
        "Docker", "Kubernetes", "Helm", "ArgoCD", "Terraform", "Ansible",
        "Jenkins", "GitLab CI", "GitHub Actions", "CI/CD", "Nginx",
        "Prometheus", "Grafana", "Linux", "Bash",
    },
    "Data": {
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "ClickHouse",
        "Kafka", "RabbitMQ", "Elasticsearch",
    },
    "ML": {
        "PyTorch", "TensorFlow", "scikit-learn", "pandas", "numpy",
        "Python",
    },
    "Mobile": {
        "Swift", "Kotlin", "Flutter",
    },
}

# Иерархия "частное -> общее": знаешь PostgreSQL значит человек знает SQL
# В обратную сторону слабее: знание SQL не гарантирует именно PostgreSQL
SKILL_PARENTS = {
    "PostgreSQL": {"SQL"},
    "MySQL": {"SQL"},
    "ClickHouse": {"SQL"},
    "Django": {"Python"},
    "FastAPI": {"Python"},
    "Flask": {"Python"},
    "React": {"JavaScript"},
    "Angular": {"JavaScript"},
    "Vue": {"JavaScript"},
    "PyTorch": {"Python"},
    "TensorFlow": {"Python"},
    "scikit-learn": {"Python"},
    "GitLab CI": {"CI/CD"},
    "GitHub Actions": {"CI/CD"},
    "Jenkins": {"CI/CD"},
    "ArgoCD": {"CI/CD"},
}

HIERARCHY_UP_CREDIT = 0.9    # знаю PostgreSQL, требуется SQL - почти полный зачёт
HIERARCHY_DOWN_CREDIT = 0.55  # знаю SQL, требуется PostgreSQL - только частичный

# навык -> в какие домены он входит, удобно спрашивать "родственны ли два навыка"
_SKILL_TO_GROUPS = {}
for _group, _skills in SKILL_GROUPS.items():
    for _s in _skills:
        _SKILL_TO_GROUPS.setdefault(_s, set()).add(_group)

# все навыки, которые мы знаем "в лицо" по этому списку отсекаем мусор
KNOWN_SKILLS = set(_SKILL_TO_GROUPS.keys()) | set(SKILL_SYNONYMS.values())


def canonicalize(skill):
    """
    Сводим разные написания одного навыка к одному виду: k8s и kuber -> Kubernetes
    Нужно, чтобы синонимы не считались разными навыками при сравнении
    Если программисты по разному называют одни и те же технологии, фреймворки
    """
    if not skill:
        return None
    key = skill.strip().lower()
    if key in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[key]
    for known in KNOWN_SKILLS:
        if known.lower() == key:
            return known
    return skill.strip()


def is_probable_skill(text):
    """
    Отсекаем мусор, который модель иногда метит как навык: куски email,
    телефонов, обрывки доменов. Без этого в навыки лезли "artem." и "protonmail. com"
    todo исправить распознавание Ozon Tech как образование
    """
    if not text:
        return False
    t = text.strip()
    if len(t) < 2:
        return False
    known_lower = {k.lower() for k in KNOWN_SKILLS}
    # пропускаем с точкой внутри (node.js, scikit-learn)
    if t.lower() in known_lower:
        return True
    # явная почта или ссылка
    if "@" in t or "://" in t:
        return False
    if re.search(r"\.(com|ru|org|net|io|dev)\b", t.lower()):
        return False
    # обрывок почты/домена: латиница в нижнем регистре с точкой ("artem.", "gmail.com")
    if "." in t and re.fullmatch(r"[a-z0-9.\-_+\s]+", t.lower()):
        return False
    # одни цифры и разделители - это телефон, а не навык
    if re.fullmatch(r"[\d\s\-()+]+", t):
        return False
    return True


def groups_of(skill):
    """К каким доменам (Backend, Data или DevOps) относится навык"""
    return _SKILL_TO_GROUPS.get(canonicalize(skill), set())


def are_related(skill_a, skill_b):
    """Родственны ли навыки - то есть сидят ли хотя бы в одном общем домене"""
    a = canonicalize(skill_a)
    b = canonicalize(skill_b)
    if a == b:
        return True
    ga, gb = groups_of(a), groups_of(b)
    return bool(ga & gb)


def hierarchy_credit(candidate_skill, required_skill):
    """
    Зачёт по линии "частное-общее" между навыком кандидата и требованием

    Знает PostgreSQL, нужен SQL значит даём почти полный зачёт
    и наоборот если знает SQL, а нужен PostgreSQL) значит зачет только частичный. Если связи нет, возвращаем 0
    """
    c = canonicalize(candidate_skill)
    r = canonicalize(required_skill)
    if r in SKILL_PARENTS.get(c, set()):
        return HIERARCHY_UP_CREDIT
    if c in SKILL_PARENTS.get(r, set()):
        return HIERARCHY_DOWN_CREDIT
    return 0.0


def dominant_domain(skills):
    """Главный домен кандидата - чей домен чаще встречается в навыках, тот и Backend/DevOps/ML"""
    counts = {}
    for s in skills:
        for g in groups_of(s):
            counts[g] = counts.get(g, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)
