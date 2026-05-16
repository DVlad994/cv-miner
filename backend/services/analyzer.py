import re

import torch
from transformers import AutoTokenizer, AutoModel, PreTrainedModel, PreTrainedTokenizer

MODEL_NAME = "DeepPavlov/rubert-base-cased"


print("Загрузка RuBERT...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()
    print("RuBERT загружен.")
except Exception as e:
    print(f"Ошибка загрузки RuBERT: {e}")
    print("Работаем в режиме без нейросети (только правила).")



def extract_entities(text: str) -> dict:
    """
    Извлекает сущности из текста, используя правила + RuBERT для верификации
    """
    result = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": [],
        "experience_years": None,
        "last_position": None
    }

    # вручную написали правила для email, номера телефона
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?\d[\d\s\-\(\)]{6,}\d'

    email_match = re.search(email_pattern, text)
    if email_match:
        result["email"] = email_match.group(0)

    phone_match = re.search(phone_pattern, text)
    if phone_match:
        result["phone"] = phone_match.group(0).strip()

    # Извлечение ФИО
    lines = text.split('\n')
    name_candidates = []
    for line in lines[:10]:
        line = line.strip()
        if '@' in line or re.search(r'[\d\s\-()]{6,}', line):
            continue
        words = line.split()
        if 2 <= len(words) <= 3 and all(w[0].isupper() for w in words if w):
            if not any(keyword in line.lower() for keyword in ['разработчик', 'developer', 'менеджер', 'аналитик']):
                name_candidates.append(line)

    if name_candidates:
        result["name"] = name_candidates[0]

    # Извлечение навыков
    skills_keywords = [
        "Python", "Django", "DRF", "FastAPI", "Flask", "PostgreSQL", "Redis",
        "Docker", "Docker Compose", "Kubernetes", "Git", "GitLab", "CI/CD",
        "Linux", "Ubuntu", "CentOS", "Bash", "Nginx", "SQL", "MySQL",
        "MongoDB", "Elasticsearch", "RabbitMQ", "Celery", "JavaScript",
        "TypeScript", "React", "Vue", "Angular", "HTML", "CSS", "REST API",
        "GraphQL", "WebSocket", "pytest", "unittest", "Scrapy", "BeautifulSoup",
        "aiogram", "Pandas", "NumPy", "Machine Learning", "Deep Learning",
        "PyTorch", "TensorFlow", "AWS", "GCP", "Azure", "Terraform", "Ansible",
        "Tableau", "Power BI", "Jira", "Confluence", "Agile", "Scrum"
    ]

    text_lower = text.lower()
    found_skills = []
    for skill in skills_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    result["skills"] = found_skills

    # Извлекаем последнюю должность
    position_keywords = [
        "разработчик", "developer", "инженер", "engineer", "аналитик", "analyst",
        "менеджер", "manager", "devops", "team lead", "архитектор", "architect"
    ]

    for line in lines:
        line_lower = line.lower()
        for keyword in position_keywords:
            if keyword in line_lower:
                result["last_position"] = line.strip()
                break
        if result["last_position"]:
            break

    # Извлекаем опыт работы
    experience_patterns = [
        r'(\d+)\s*(?:год|года|лет|year|years).*?опыт',
        r'опыт.*?(\d+)\s*(?:год|года|лет|year|years)',
        r'(\d+)\s*(?:год|года|лет|year|years)'
    ]

    for pattern in experience_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                result["experience_years"] = float(match.group(1))
                break
            except ValueError:
                pass

    return result


def get_embedding(text: str) -> torch.Tensor:
    """
    Преобразует текст в векторное представление (768 чисел)
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

    # Усредняем скрытые состояния всех токенов (mean pooling)
    attention_mask = inputs["attention_mask"]
    hidden_states = outputs.last_hidden_state

    mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
    sum_embeddings = torch.sum(hidden_states * mask_expanded, dim=1)
    sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    embedding = sum_embeddings / sum_mask

    return embedding


def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    """Вычисляет косинусное сходство между двумя векторами"""
    a_norm = a / a.norm(dim=1, keepdim=True)
    b_norm = b / b.norm(dim=1, keepdim=True)
    return float((a_norm * b_norm).sum())


def match_skills(resume_skills: list, vacancy_text: str) -> dict:
    """
    Сравнивает навыки из резюме с требованиями в выбранной вакансии,
    а возвращает совпадения и недостающие навыки
    """
    # Извлекаем навыки из вакансии
    vacancy_skills = []
    for word in vacancy_text.replace(',', ' ').split():
        word = word.strip()
        if word and len(word) > 1 and word[0].isupper():
            vacancy_skills.append(word)

    if not vacancy_skills:
        vacancy_skills = [s.strip() for s in vacancy_text.split(',') if s.strip()]

    matched = []
    missing = []

    for req in vacancy_skills:
        req_lower = req.lower()
        found = False
        for skill in resume_skills:
            if skill.lower() in req_lower or req_lower in skill.lower():
                matched.append(req)
                found = True
                break
        if not found:
            missing.append(req)

    total = len(vacancy_skills)
    matched_count = len(matched)
    score = round((matched_count / total) * 100, 1) if total > 0 else 0

    return {
        "total_score": score,
        "matched": matched,
        "missing": missing
    }


def analyze_resume_text(resume_text: str, vacancy_text: str) -> dict:
    """
    анализ резюме: берём сущности и сравниваем
    """
    entities = extract_entities(resume_text)
    matching = match_skills(entities["skills"], vacancy_text)

    return {
        "candidate": entities,
        "matching_result": matching
    }