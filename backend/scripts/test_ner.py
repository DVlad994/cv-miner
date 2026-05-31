import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.analyzer import (
    extract_entities, analyze_resume_text, ner_model, NER_MODEL_PATH
)

print(f"Модель загружена: {ner_model is not None}")
print(f"Путь к модели: {NER_MODEL_PATH}")

text = """Артём Власов

Email: artem.vlsv@protonmail.com

Город: Казань

Навыки:
PyTorch
RabbitMQ
Grafana
Prometheus
ClickHouse
Go
Python
Helm
ArgoCD
SQL
Docker
Kubernetes
PostgreSQL

Опыт работы:

2019 - 2021
Python-разработчик, Тинькофф
Разработка и поддержка внутренней платформы обработки данных, ускорил пайплайн на 50%

2021 - настоящее время
Team Lead, Ozon Tech
Руководство командой backend/platform engineering, снизил расходы на 20%

Образование:
КФУ
Институт вычислительной математики и информационных технологий

Английский - Upper-Intermediate
"""

result = extract_entities(text)
print("\nИзвлечённые сущности:")
for key, value in result.items():
    print(f"  {key}: {value}")

vacancy = "Python, Django, PostgreSQL, Docker, Git\nОпыт от 3 лет"
analysis = analyze_resume_text(text, vacancy)

print("\nПрофиль кандидата:")
for key, value in analysis["profile"].items():
    print(f"  {key}: {value}")

mr = analysis["matching_result"]
print(f"\nИтоговый балл: {mr['total_score']}%  (только навыки: {mr['skills_score']}%)")
print(f"  Факторы: {mr['factors']}")
print(f"  Совпало: {mr['matched']}")
print(f"  Частично: {mr['partial']}")
print(f"  Отсутствует: {mr['missing']}")
