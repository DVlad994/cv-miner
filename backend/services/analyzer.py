import os
import re
from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForTokenClassification

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
    merged = ""
    for token in tokens:
        if token.startswith("##"):
            merged += token[2:]
        else:
            if merged:
                merged += " "
            merged += token
    return merged.strip()


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
        "organizations": [], "education": [], "dates": []
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
        if token.startswith("##"):
            token = token[2:]

        if label.startswith("B-"):
            if current_tokens:
                merged = merge_wordpiece_tokens(current_tokens)
                entities.append((current_label, merged))
            current_label = label[2:]
            current_tokens = [token]
        elif label.startswith("I-") and current_label == label[2:]:
            current_tokens.append(token)
        else:
            if current_tokens:
                merged = merge_wordpiece_tokens(current_tokens)
                entities.append((current_label, merged))
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
            if entity_text not in result["skills"] and len(entity_text) > 1:
                result["skills"].append(entity_text)
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


def match_skills(resume_skills, vacancy_text):
    """
    Сравнивает навыки из резюме с требованиями вакансии
    """
    vacancy_skills = [line.strip() for line in vacancy_text.split("\n") if line.strip()]
    if not vacancy_skills:
        vacancy_skills = [s.strip() for s in vacancy_text.split(",") if s.strip()]

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
    score = round((len(matched) / total) * 100, 1) if total > 0 else 0
    return {"total_score": score, "matched": matched, "missing": missing}


def analyze_resume_text(resume_text, vacancy_text):
    """
    Анализ резюме: извлекаем сущности и сравниваем навыки
    """
    entities = extract_entities(resume_text)
    matching = match_skills(entities["skills"], vacancy_text)
    return {"candidate": entities, "matching_result": matching}