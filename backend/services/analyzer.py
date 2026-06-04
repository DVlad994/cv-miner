import os
import re
from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForTokenClassification

from services import skills_ontology as onto

EMBEDDING_MODEL_NAME = "DeepPavlov/rubert-base-cased"
NER_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "rubert-ner-resume"))

print("Загрузка RuBERT...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
try:
    tokenizer = AutoTokenizer.from_pretrained(NER_MODEL_PATH)
    embedding_model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME).to(device)
    ner_model = AutoModelForTokenClassification.from_pretrained(
        NER_MODEL_PATH
    ).to(device)
    embedding_model.eval()
    ner_model.eval()
    print(f"RuBERT загружен. Device: {device}")
except Exception as e:
    print(f"Ошибка загрузки RuBERT: {e}")
    tokenizer = None
    embedding_model = None
    ner_model = None

def merge_wordpiece_tokens(tokens):
    words = []
    for token in tokens:
        if token.startswith("##"):
            if words:
                words[-1] += token[2:]
        else:
            words.append(token)
    return " ".join(words)


def clean_entity_text(text):
    text = re.sub(r"\s+", " ", text.strip())
    text = text.replace(" .", ".").replace(" ,", ",").replace(" :", ":").replace(" ;", ";")
    text = text.replace(" - ", "-").replace(" — ", " — ")
    # Склеиваем разорванные токены
    fixes = {}
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)
    return text


def extract_entities(text):
    result = {
        "name": None, "email": None, "phone": None,
        "skills": [], "experience_years": None, "last_position": None,
        "organizations": [], "education": [], "dates": [],
        "achievements": []
    }

    if ner_model is None:
        return result

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = ner_model(**inputs)

    predictions = torch.argmax(outputs.logits, dim=-1)[0]
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    labels = [ner_model.config.id2label[p.item()] for p in predictions]

    entities = []
    current_tokens = []
    current_label = None

    for token, label in zip(tokens, labels):
        if token in ["[CLS]", "[SEP]", "[PAD]"]:
            continue

        # ## подтокены всегда продолжают текущую сущность,
        # независимо от того, что предсказала модель
        if token.startswith("##"):
            if current_tokens:
                current_tokens.append(token)
            continue

        if label.startswith("B-"):
            if current_tokens:
                entities.append((current_label, merge_wordpiece_tokens(current_tokens)))
            current_label = label[2:]
            current_tokens = [token]

        elif label.startswith("I-") and current_label == label[2:]:
            current_tokens.append(token)

        else:
            if current_tokens:
                entities.append((current_label, merge_wordpiece_tokens(current_tokens)))

            current_tokens = []
            current_label = None

    if current_tokens:
        merged = merge_wordpiece_tokens(current_tokens)
        entities.append((current_label, merged))

    for entity_type, entity_text in entities:
        entity_text = clean_entity_text(entity_text)
        if not entity_text:
            continue
        if len(entity_text) <= 1 and entity_type != "DATE":
            continue

        if entity_type == "NAME" and result["name"] is None:
            result["name"] = entity_text
        elif entity_type == "EMAIL":
            match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", entity_text)
            if match:
                result["email"] = match.group(0)
        elif entity_type == "PHONE":
            match = re.search(r"\+?\d[\d\-()\s]{8,}\d", entity_text)
            if match:
                result["phone"] = match.group(0)
        elif entity_type == "SKILL":
            cleaned_skill = entity_text.strip()
            # Отсекаем мусор (части email/телефонов) и канонизируем синонимы
            if cleaned_skill and onto.is_probable_skill(cleaned_skill):
                canon = onto.canonicalize(cleaned_skill)
                if canon and canon not in result["skills"]:
                    result["skills"].append(canon)
        elif entity_type == "POS" and result["last_position"] is None:
            result["last_position"] = entity_text
        elif entity_type == "ORG":
            if entity_text not in result["organizations"] and len(entity_text) > 1:
                result["organizations"].append(entity_text)
        elif entity_type == "EDU":
            if entity_text not in result["education"] and len(entity_text) > 1:
                result["education"].append(entity_text)
        elif entity_type == "DATE":
            if entity_text not in result["dates"]:
                result["dates"].append(entity_text)
        elif entity_type == "ACHIEVEMENT":
            if entity_text not in result["achievements"] and len(entity_text) > 3:
                result["achievements"].append(entity_text)

    # Fallback для дат: периоды вида "2019 - 2021", "2021 - настоящее время"
    if not result["dates"]:
        for m in re.findall(r"\b(20\d{2}|19\d{2})\s*[—\-–]\s*(20\d{2}|настоящее время|наст\.?\s*время)",
                            text, re.IGNORECASE):
            period = f"{m[0]} — {m[1]}"
            if period not in result["dates"]:
                result["dates"].append(period)

    # Считаем опыт
    years = []
    for d in result["dates"]:
        for y in re.findall(r"\d{4}", d):
            try:
                years.append(int(y))
            except ValueError:
                pass
    current_year = datetime.now().year
    if "настоящее время" in " ".join(result["dates"]).lower():
        years.append(current_year)
    if len(years) >= 2:
        result["experience_years"] = max(years) - min(years)

    # Fallback
    if result["email"] is None:
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if match:
            result["email"] = match.group(0)
    if result["phone"] is None:
        match = re.search(r"\+?\d[\d\-()\s]{8,}\d", text)
        if match:
            result["phone"] = match.group(0)
    if result["name"] is None:
        for line in text.split("\n")[:5]:
            line = line.strip()
            if "@" in line:
                continue
            words = line.split()
            if 2 <= len(words) <= 3 and all(len(w) > 1 and w[0].isupper() for w in words):
                result["name"] = line
                break

    # Fallback / augmentation: количественные достижения по тексту строк
    achievement_patterns = [
        r"[^.\n]*\b(?:увеличил|снизил|сократил|ускорил|оптимизировал|повысил|вырос\w*)\w*[^.\n]*?\d+\s*%[^.\n]*",
        r"[^.\n]*\d+\s*%[^.\n]*",
        r"[^.\n]*\bс\s+\d+\s+до\s+\d+[^.\n]*",
        r"[^.\n]*команд\w*\s+из\s+\d+[^.\n]*",
    ]
    for pat in achievement_patterns:
        for m in re.findall(pat, text, flags=re.IGNORECASE):
            phrase = clean_entity_text(m)
            if phrase and phrase not in result["achievements"] and len(phrase) > 3:
                result["achievements"].append(phrase)

    return result


def get_embedding(text):
    """
    Преобразует текст в векторное представление (768 чисел)
    """
    if embedding_model is None:
        raise RuntimeError("Embedding model not loaded")
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = embedding_model(**inputs)
    attention_mask = inputs["attention_mask"]
    hidden = outputs.last_hidden_state
    mask = attention_mask.unsqueeze(-1).expand(hidden.size()).float()
    pooled = (hidden * mask).sum(1) / mask.sum(1)
    return pooled.cpu()


def cosine_similarity(a, b):
    """
    Вычисляет косинусное сходство между двумя векторами
    """
    a = a / a.norm(dim=1, keepdim=True)
    b = b / b.norm(dim=1, keepdim=True)
    return float((a * b).sum())


# Кэш эмбеддингов навыков (чтобы не считать один и тот же навык много раз)
_EMB_CACHE = {}


def _cached_embedding(text):
    key = text.strip().lower()
    if key not in _EMB_CACHE:
        _EMB_CACHE[key] = get_embedding(text)
    return _EMB_CACHE[key]


def skill_similarity(skill_a, skill_b):
    """
    Семантическая близость двух навыков [0..1]
    """
    a = onto.canonicalize(skill_a)
    b = onto.canonicalize(skill_b)
    if a.lower() == b.lower():
        return 1.0
    if embedding_model is None:
        return 0.0
    try:
        sim = cosine_similarity(_cached_embedding(a), _cached_embedding(b))
    except Exception:
        return 0.0
    # Косинус RuBERT обычно лежит высоко (0.5..0.95), поэтому растягиваем
    return max(0.0, min(1.0, (sim - 0.5) / 0.45))


# Насколько закрыто одно требование вакансии: от этих порогов зависит,
# попадёт навык в "совпало", "частично" или "отсутствует"
FULL_CREDIT = 0.9      # считаем требование полностью закрытым
PARTIAL_CREDIT = 0.4   # ниже этого уже "отсутствует"
RELATED_CREDIT = 0.6   # навык из того же домена, но не та же технология


def parse_vacancy(vacancy_text):
    """
    Достаём из текста вакансии список навыков и требуемый опыт

    HR обычно пишет вакансию вперемешку: навыки через запятую плюс строки
    вроде "Опыт от 3 лет" — опыт вытаскиваем отдельно, а такие мета-строки
    в навыки не пускаем, иначе "Опыт от 3 лет" улетит в "отсутствует"
    """
    required_experience = None
    m = re.search(r"(?:опыт\D{0,15})(\d+)\s*(?:\+|лет|год)", vacancy_text, re.IGNORECASE)
    if m:
        required_experience = int(m.group(1))

    # строки про опыт/образование/зарплату это не навыки — отсекаем
    meta_re = re.compile(r"опыт|образован|зарплат|з/п|занятост|график|релокац", re.IGNORECASE)
    raw_items = []
    for line in vacancy_text.split("\n"):
        raw_items.extend(line.split(","))
    skills = [item.strip() for item in raw_items
              if item.strip() and not meta_re.search(item)]

    return {"skills": skills, "required_experience": required_experience}


def _best_credit(req, resume_skills):
    """
    Ищем, чем из навыков кандидата лучше всего закрыть требование req

    Идём от точного совпадения к более слабым: та же технология (1.0),
    иерархия частное-общее (PostgreSQL закрывает SQL), один домен, и в крайнем
    случае близость по эмбеддингам. Возвращаем лучший зачёт и через какой навык
    """
    req_canon = onto.canonicalize(req)
    best, best_skill = 0.0, None
    for skill in resume_skills:
        s_canon = onto.canonicalize(skill)
        if s_canon.lower() == req_canon.lower():
            return 1.0, skill
        credit = 0.0
        # PostgreSQL <-> SQL, Django <-> Python и т.п.
        credit = max(credit, onto.hierarchy_credit(s_canon, req_canon))
        if onto.are_related(s_canon, req_canon):
            credit = max(credit, RELATED_CREDIT)
        # последняя попытка — насколько навыки близки семантически
        sim = skill_similarity(s_canon, req_canon)
        credit = max(credit, sim * 0.8)
        if credit > best:
            best, best_skill = credit, skill
    return best, best_skill


def match_skills(resume_skills, vacancy_text):
    """
    Раскладываем требования вакансии на совпало/частично/отсутствует

    Главная фишка против тупого поиска по словам: Django засчитается через
    Python, а k8s и Kubernetes считаются одним навыком
    """
    vacancy = parse_vacancy(vacancy_text)
    vacancy_skills = vacancy["skills"]

    matched, partial, missing = [], [], []
    total_credit = 0.0

    for req in vacancy_skills:
        credit, via = _best_credit(req, resume_skills)
        total_credit += credit
        if credit >= FULL_CREDIT:
            matched.append(req)
        elif credit >= PARTIAL_CREDIT:
            partial.append({"requirement": req, "via": via, "credit": round(credit, 2)})
        else:
            missing.append(req)

    total = len(vacancy_skills)
    score = round((total_credit / total) * 100, 1) if total > 0 else 0.0
    return {
        "skills_score": score,
        "matched": matched,
        "partial": partial,
        "missing": missing,
    }


def build_candidate_profile(entities):
    """
    Собираем короткую карточку кандидата для верхушки результата и для рейтинга:
    уровень, домен, опыт - то, по чему реальный HR-менеджер прикидывает человека за пару секунд
    """
    skills = entities.get("skills", [])
    exp = entities.get("experience_years")
    domain = onto.dominant_domain(skills)

    pos = (entities.get("last_position") or "").lower()
    leadership = any(k in pos for k in ["lead", "лид", "тимлид", "head", "руковод", "директор", "manager"])
    if exp is None:
        level = "Unknown"
    elif exp < 1.5:
        level = "Junior"
    elif exp < 3:
        level = "Middle"
    elif exp < 6:
        level = "Senior"
    else:
        level = "Lead" if leadership else "Senior"

    education = "Higher" if entities.get("education") else "Unknown"

    return {
        "level": level,
        "domain": domain,
        "skills": skills,
        "experience": exp,
        "leadership": leadership,
        "education": education,
        "achievements": entities.get("achievements", []),
    }


# Вес каждого фактора в итоговом балле - навыки решают, но не на 100%,
# иначе сильный по опыту и достижениям кандидат проседал бы из-за одного навыка
SCORE_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.25,
    "achievements": 0.20,
    "education": 0.10,
    "position": 0.05,
}


def score_resume(entities, vacancy_text):
    """
    Считаем итоговый балл 0-100 как взвешенную сумму факторов

    Не просто "сколько навыков совпало", а ещё опыт, достижения, образование
    и насколько прошлая должность бьётся с вакансией
    """
    profile = build_candidate_profile(entities)
    vacancy = parse_vacancy(vacancy_text)
    skill_match = match_skills(entities["skills"], vacancy_text)

    # навыки уже посчитаны в match_skills, просто переводим в долю
    skills_factor = skill_match["skills_score"] / 100.0

    # опыт: если вакансия задала планку - меряем относительно неё,
    # если нет - считаем 5 лет за "полный балл"
    req_exp = vacancy["required_experience"]
    cand_exp = profile["experience"]
    if cand_exp is None:
        experience_factor = 0.5  # опыт не распознали — не наказываем и не премируем
    elif req_exp:
        experience_factor = max(0.0, min(1.0, cand_exp / req_exp))
    else:
        experience_factor = max(0.0, min(1.0, cand_exp / 5.0))

    # достижения с цифрами ("ускорил на 50%") - сильный сигнал, что человек про результат,
    # трех достижений уже хватает на полный балл
    n_ach = len(profile["achievements"])
    achievements_factor = min(1.0, n_ach / 3.0)

    education_factor = 1.0 if profile["education"] == "Higher" else 0.5

    # насколько последняя должность близка к вакансии (по эмбеддингам);
    # если должность не распознали - ставим нейтральные 0.5
    position_factor = 0.5
    if entities.get("last_position"):
        try:
            sim = cosine_similarity(
                _cached_embedding(entities["last_position"]),
                _cached_embedding(vacancy_text),
            )
            position_factor = max(0.0, min(1.0, (sim - 0.5) / 0.45))
        except Exception:
            position_factor = 0.5

    factors = {
        "skills": round(skills_factor, 3),
        "experience": round(experience_factor, 3),
        "achievements": round(achievements_factor, 3),
        "education": round(education_factor, 3),
        "position": round(position_factor, 3),
    }
    total = sum(SCORE_WEIGHTS[k] * factors[k] for k in SCORE_WEIGHTS)
    total_score = round(total * 100, 1)

    # сразу прикладываем разбор балла, чтобы HR видел не голую цифру
    explanation = explain_score(factors, skill_match, profile, req_exp)

    return {
        "total_score": total_score,
        "skills_score": skill_match["skills_score"],
        "factors": factors,
        "weights": SCORE_WEIGHTS,
        "matched": skill_match["matched"],
        "partial": skill_match["partial"],
        "missing": skill_match["missing"],
        "explanation": explanation,
    }


# как подписывать факторы в интерфейсе
FACTOR_LABELS = {
    "skills": "Совпадение навыков",
    "experience": "Опыт работы",
    "achievements": "Достижения",
    "education": "Образование",
    "position": "Релевантность должности",
}


def explain_score(factors, skill_match, profile, req_exp):
    """
    Разбираем итоговый балл на части, чтобы было видно почему именно такая итоговая цифра

    Чтобы не доверять голой цифре + видеть подробный анализ показываем вклад каждого фактора в баллах
    и пишем словами, что нашли по навыкам, опыту, достижениям и образованию
    """
    breakdown = []
    for key, weight in SCORE_WEIGHTS.items():
        contribution = round(weight * factors[key] * 100, 1)  # сколько баллов реально дал фактор
        breakdown.append({
            "factor": key,
            "label": FACTOR_LABELS.get(key, key),
            "value": factors[key],            # 0..1, насколько фактор закрыт
            "weight": weight,
            "contribution": contribution,     # вклад в total_score
            "max_contribution": round(weight * 100, 1),  # потолок этого фактора
        })
    # сортируем по вкладу, чтобы наверху было то, что реально тянет балл
    breakdown.sort(key=lambda x: x["contribution"], reverse=True)

    notes = []
    n_matched = len(skill_match["matched"])
    n_partial = len(skill_match["partial"])
    n_missing = len(skill_match["missing"])
    notes.append(
        f"Навыки: {n_matched} полностью, {n_partial} частично, {n_missing} отсутствует"
    )
    # показываем живой пример частичного зачёта, чтобы было понятно, как он работает
    if skill_match["partial"]:
        ex = skill_match["partial"][0]
        notes.append(
            f"Частичный зачёт, например «{ex['requirement']}» — через «{ex['via']}» "
            f"({int(ex['credit'] * 100)} %)"
        )
    exp = profile.get("experience")
    if exp is not None:
        if req_exp:
            notes.append(f"Опыт {exp} лет при требовании от {req_exp} лет")
        else:
            notes.append(f"Опыт работы: {exp} лет")
    n_ach = len(profile.get("achievements", []))
    if n_ach:
        notes.append(f"Найдено достижений с измеримым результатом: {n_ach}")
    else:
        notes.append("Количественные достижения в резюме не обнаружены")
    if profile.get("education") == "Higher":
        notes.append("Указано высшее образование")

    # одной фразой: что вытянуло балл и где главный провал
    top = breakdown[0]
    weakest = min(breakdown, key=lambda x: x["value"])
    summary = (
        f"Наибольший вклад в балл вносит фактор «{top['label']}» "
        f"(+{top['contribution']} из {top['max_contribution']} возможных). "
        f"Слабее всего закрыт фактор «{weakest['label']}»"
    )

    return {"summary": summary, "breakdown": breakdown, "notes": notes}


def analyze_resume_text(resume_text, vacancy_text):
    """
    Полный прогон одного резюме: сущности -> профиль -> балл
    Это то, что дергает эндпоинт /api/analyze
    """
    entities = extract_entities(resume_text)
    profile = build_candidate_profile(entities)
    matching = score_resume(entities, vacancy_text)
    return {
        "candidate": entities,
        "profile": profile,
        "matching_result": matching,
    }


def rank_resumes(resumes, vacancy_text):
    """
    Прогоняем пачку резюме по одной вакансии и сортируем по баллу

    Главный сценарий HR: загрузил стопку откликов, получил готовый рейтинг,
    кого смотреть первым. resumes — это список {"filename", "text"}
    """
    results = []
    for item in resumes:
        analysis = analyze_resume_text(item["text"], vacancy_text)
        results.append({
            "filename": item.get("filename"),
            "candidate_name": analysis["candidate"].get("name"),
            "total_score": analysis["matching_result"]["total_score"],
            "skills_score": analysis["matching_result"]["skills_score"],
            "level": analysis["profile"].get("level"),
            "domain": analysis["profile"].get("domain"),
            "matched": analysis["matching_result"]["matched"],
            "partial": analysis["matching_result"]["partial"],
            "missing": analysis["matching_result"]["missing"],
            "candidate": analysis["candidate"],
            "profile": analysis["profile"],
            "matching_result": analysis["matching_result"],
        })

    # лучший балл наверх и проставляем места 1, 2, 3...
    results.sort(key=lambda r: r["total_score"], reverse=True)
    for i, r in enumerate(results, start=1):
        r["rank"] = i
    return results