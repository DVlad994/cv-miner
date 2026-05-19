import pandas as pd

CSV_PATH = "train.csv"

IT_KEYWORDS = [
    "developer", "engineer", "devops", "sre", "qa engineer", "qa automation",
    "data scientist", "data analyst", "data engineer", "ml engineer",
    "machine learning", "backend", "frontend", "fullstack",
    "software", "программист", "architect",
    "ios", "android", "мобильный разработчик",
    "python", "java", "javascript", "typescript", "golang",
    "react", "angular", "vue", "node.js", "django",
    "разработчик", "тестировщик", "devops инженер",
    "team lead", "tech lead", "системный администратор",
    "бэкенд", "фронтенд", "фуллстек", "веб-разработчик",
    "кибербезопасности", "пентестер", "big data", "etl",
]

df = pd.read_csv(CSV_PATH, sep="|", engine="python", encoding="utf-8", on_bad_lines="skip")
print(f"Всего строк: {len(df)}")

it_mask = df["positionName"].apply(
    lambda x: any(kw in str(x).lower() for kw in IT_KEYWORDS) if pd.notna(x) else False
)

it_df = df[it_mask]
print(f"IT-резюме: {len(it_df)}")

# Уникальные должности
positions = it_df["positionName"].dropna().unique()
print(f"\nУникальных IT-должностей: {len(positions)}")