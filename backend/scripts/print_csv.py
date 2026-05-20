import pandas as pd
import json

CSV_PATH = "train.csv"

IT_KEYWORDS = [
    "разработчик", "developer", "программист", "software engineer",
    "devops", "data scientist", "data engineer", "data analyst",
    "qa engineer", "qa automation", "тестировщик", "frontend",
    "backend", "fullstack", "machine learning", "ml engineer",
    "ios developer", "android developer", "системный аналитик",
    "team lead", "tech lead", "веб-разработчик", "big data",
    "etl разработчик", "bi аналитик", "кибербезопасности", "пентестер",
]

df = pd.read_csv(CSV_PATH, sep="|", engine="python", encoding="utf-8", on_bad_lines="skip")
print(f"Всего строк: {len(df)}")

def has_it_work_experience(work_json):
    """
    Поверяет есть ли опыт работы по специальности
    """
    if pd.isna(work_json):
        return False
    try:
        works = json.loads(work_json.replace('""', '"'))
        for w in works:
            title = w.get("jobTitle", "").lower()
            if any(kw in title for kw in IT_KEYWORDS):
                return True
    except:
        pass
    return False

def has_it_skills(skills_json):
    """
    Проверяет, есть ли технические навыки
    """
    if pd.isna(skills_json):
        return False
    try:
        skills = json.loads(skills_json.replace('""', '"'))
        tech_skills = {"python", "java", "javascript", "typescript", "react", "angular",
                      "vue", "django", "docker", "kubernetes", "git", "sql", "linux",
                      "aws", "azure", "c++", "c#", "php", "ruby", "go", "rust",
                      "node.js", "spring", "flutter", "swift", "kotlin"}
        for s in skills:
            if isinstance(s, str) and s.lower() in tech_skills:
                return True
    except:
        pass
    return False

it_mask = df.apply(
    lambda row: has_it_work_experience(row.get("workExperienceList")) or
                has_it_skills(row.get("hardSkills_cv")),
    axis=1
)

it_df = df[it_mask]

cols = ["positionName", "hardSkills_cv", "workExperienceList"]
for i, (_, row) in enumerate(it_df.iterrows()):
    print(f"Резюме #{i+1}")
    for col in cols:
        val = row.get(col)
        if pd.notna(val):
            s = str(val)
            if len(s) > 500:
                s = s[:500] + "..."
            print(f"  {col}: {s}")
    if i >= 4:
        print(f"\nВсего в таблице: {len(it_df)} резюме (IT-специальности)")
        break