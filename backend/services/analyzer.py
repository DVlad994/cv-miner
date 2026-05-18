import re
from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForTokenClassification

EMBEDDING_MODEL_NAME = "DeepPavlov/rubert-base-cased"
NER_MODEL_PATH = "./rubert_resume_ner"

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
    print("Работаем в режиме без нейросети.")

    tokenizer = None
    embedding_model = None
    ner_model = None

def clean_token(token: str) -> str:
    return token.strip()

def extract_entities(text: str) -> dict:
    """
    Извлекает сущности из текста с помощью обученного RuBERT NER
    """
    result = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": [],
        "experience_years": None,
        "last_position": None,
        "organizations": [],
        "education": [],
        "dates": []
    }

    if ner_model is None:
        return result

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = ner_model(**inputs)

    predictions = torch.argmax(outputs.logits, dim=-1)[0]
    input_ids = inputs["input_ids"][0]

    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    labels = [
        ner_model.config.id2label[p.item()]
        for p in predictions
    ]

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
                entities.append((current_label,merge_wordpiece_tokens(current_tokens)))
            current_label = label[2:]
            current_tokens = [token]

        elif label.startswith("I-") and current_label == label[2:]:
            current_tokens.append(token)
        else:
            if current_tokens:
                entities.append((
                    current_label,
                    merge_wordpiece_tokens(current_tokens)
                ))

            current_tokens = []
            current_label = None

    if current_tokens:
        entities.append((
            current_label,
            merge_wordpiece_tokens(current_tokens)
        ))

    for entity_type, entity_text in entities:
        entity_text = entity_text.strip()
        entity_text = re.sub(r"\s+", " ", entity_text)
        entity_text = entity_text.replace(" .", ".")
        entity_text = entity_text.replace(" ,", ",")
        entity_text = entity_text.replace(" :", ":")
        entity_text = entity_text.replace(" ;", ";")
        entity_text = entity_text.replace(" - ", "-")
        entity_text = entity_text.replace(" — ", " — ")
        entity_text = entity_text.replace(" AP I", "API")
        entity_text = entity_text.replace("Post gre SQL", "PostgreSQL")
        entity_text = entity_text.replace("Fast API", "FastAPI")
        entity_text = entity_text.replace("Dock er", "Docker")
        entity_text = entity_text.replace("Ku ber net es", "Kubernetes")
        entity_text = entity_text.replace("Develop er", "Developer")
        entity_text = entity_text.replace("V K", "VK")
        entity_text = entity_text.replace("информат ика", "информатика")

        if not entity_text:
            continue

        if len(entity_text) <= 1 and entity_type not in ["DATE"]:
            continue

        if entity_type == "NAME":
            if result["name"] is None:
                result["name"] = entity_text

        elif entity_type == "EMAIL":
            email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", entity_text)
            if email_match:
                result["email"] = email_match.group(0)

        elif entity_type == "PHONE":
            phone_match = re.search(r"\+?\d[\d\-()\s]{8,}\d", entity_text)
            if phone_match:
                result["phone"] = phone_match.group(0)

        elif entity_type == "SKILL":
            cleaned_skill = entity_text.strip()
            if (
                cleaned_skill
                and cleaned_skill not in result["skills"]
                and len(cleaned_skill) > 1
            ):
                result["skills"].append(cleaned_skill)

        elif entity_type == "POS":
            if result["last_position"] is None:
                result["last_position"] = entity_text

        elif entity_type == "ORG":
            if (
                entity_text not in result["organizations"]
                and len(entity_text) > 1
            ):
                result["organizations"].append(entity_text)

        elif entity_type == "EDU":
            if (
                entity_text not in result["education"]
                and len(entity_text) > 1
            ):
                result["education"].append(entity_text)

        elif entity_type == "DATE":

            if entity_text not in result["dates"]:
                result["dates"].append(entity_text)

    years = []

    for date_text in result["dates"]:
        found_years = re.findall(r"\d{4}", date_text)
        for year in found_years:
            try:
                years.append(int(year))
            except:
                pass

    current_year = datetime.now().year
    if "настоящее время" in " ".join(result["dates"]).lower():
        years.append(current_year)
    if len(years) >= 2:
        result["experience_years"] = max(years) - min(years)

    if result["email"] is None:
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            result["email"] = email_match.group(0)

    if result["phone"] is None:
        phone_match = re.search(r"\+?\d[\d\-()\s]{8,}\d", text)
        if phone_match:
            result["phone"] = phone_match.group(0)

    if result["name"] is None:
        lines = text.split("\n")
        for line in lines[:5]:
            line = line.strip()
            if "@" in line:
                continue
            words = line.split()
            if 2 <= len(words) <= 3:

                if all(
                    len(w) > 1 and w[0].isupper()
                    for w in words
                ):
                    result["name"] = line
                    break

    return result


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

def get_embedding(text: str) -> torch.Tensor:
    """
    Преобразует текст в векторное представление (768 чисел)
    """
    if embedding_model is None:
        raise RuntimeError("Embedding model not loaded")
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = embedding_model(**inputs)

    attention_mask = inputs["attention_mask"]
    hidden_states = outputs.last_hidden_state
    mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
    sum_embeddings = torch.sum(hidden_states * mask_expanded, dim=1)
    sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    embedding = sum_embeddings / sum_mask
    return embedding.cpu()

def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    """В
    ычисляет косинусное сходство между двумя векторами
    """
    a_norm = a / a.norm(dim=1, keepdim=True)
    b_norm = b / b.norm(dim=1, keepdim=True)
    return float((a_norm * b_norm).sum())


def match_skills(resume_skills: list, vacancy_text: str) -> dict:
    """
    Сравнивает навыки из резюме с требованиями вакансии
    """
    vacancy_skills = []

    for line in vacancy_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        vacancy_skills.append(line)

    if not vacancy_skills:
        vacancy_skills = [
            s.strip()
            for s in vacancy_text.split(",")
            if s.strip()
        ]

    matched = []
    missing = []

    for req in vacancy_skills:
        req_lower = req.lower()
        found = False
        for skill in resume_skills:
            skill_lower = skill.lower()
            if skill_lower in req_lower or req_lower in skill_lower:
                matched.append(req)
                found = True
                break
        if not found:
            missing.append(req)

    total = len(vacancy_skills)
    score = round((len(matched) / total) * 100, 1) if total > 0 else 0

    return {
        "total_score": score,
        "matched": matched,
        "missing": missing
    }


def analyze_resume_text(resume_text: str, vacancy_text: str) -> dict:
    """
    Анализ резюме: извлекаем сущности и сравниваем навыки
    """
    entities = extract_entities(resume_text)
    matching = match_skills(
        entities["skills"],
        vacancy_text
    )
    return {
        "candidate": entities,
        "matching_result": matching
    }