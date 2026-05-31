"""
Онтология навыков: канонизация синонимов, группировка по доменам,
фильтрация мусора и базовый граф близости технологий
Принцип работы всех современных ИИ-анализаторов резюме

  - очистка извлечённых навыков от мусора (части email, телефонов и т.п.)
  - приведения синонимов к канону (k8s -> Kubernetes)
  - зачёт родственных технологий (Django ~ FastAPI)
"""

import re

# Канонические синонимы: alias -> каноническое имя
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

# Группы навыков для частичного зачета родственных технологий
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

# Обратный индекс: канонический навык -> множество доменов
_SKILL_TO_GROUPS = {}
for _group, _skills in SKILL_GROUPS.items():
    for _s in _skills:
        _SKILL_TO_GROUPS.setdefault(_s, set()).add(_group)

# Множество всех известных канонических навыков (для фильтрации мусора)
KNOWN_SKILLS = set(_SKILL_TO_GROUPS.keys()) | set(SKILL_SYNONYMS.values())


def canonicalize(skill):
    """
    Приводит навык к каноническому виду через словарь синонимов
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
    Фильтр мусора: отсекает части email/телефонов/URL и слишком короткие
    бессмысленные фрагменты, которые ошибочно размечены как навык
    """
    if not text:
        return False
    t = text.strip()
    if len(t) < 2:
        return False
    known_lower = {k.lower() for k in KNOWN_SKILLS}
    # Известный навык - всегда пропускаем (даже если есть точка: node.js, scikit-learn)
    if t.lower() in known_lower:
        return True
    # Части email / адресов / ссылок
    if "@" in t or "://" in t:
        return False
    if re.search(r"\.(com|ru|org|net|io|dev)\b", t.lower()):
        return False
    # Огрызок email/домена: латиница в нижнем регистре с точкой
    # ("artem.", "vlsv", "protonmail. com") и это не известный навык
    if "." in t and re.fullmatch(r"[a-z0-9.\-_+\s]+", t.lower()):
        return False
    # Телефонные грызки
    if re.fullmatch(r"[\d\s\-()+]+", t):
        return False
    return True


def groups_of(skill):
    """
    Возвращает множество доменов, к которым относится навык
    """
    return _SKILL_TO_GROUPS.get(canonicalize(skill), set())


def are_related(skill_a, skill_b):
    """
    :param skill_a:
    :param skill_b:
    :return: True, если навыки делят хотя бы один домен (родственные технологии)
    """
    a = canonicalize(skill_a)
    b = canonicalize(skill_b)
    if a == b:
        return True
    ga, gb = groups_of(a), groups_of(b)
    return bool(ga & gb)


def dominant_domain(skills):
    """
    Определяет основной домен кандидата по списку навыков
    """
    counts = {}
    for s in skills:
        for g in groups_of(s):
            counts[g] = counts.get(g, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)
