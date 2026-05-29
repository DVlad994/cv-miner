from backend.services.analyzer import extract_entities, ner_model, NER_MODEL_PATH

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

2019 — 2021
Python-разработчик, Тинькофф
Разработка и поддержка внутренней платформы обработки данных

2021 — настоящее время
Team Lead, Ozon Tech
Руководство командой backend/platform engineering

Образование:
КФУ
Институт вычислительной математики и информационных технологий

Английский — Upper-Intermediate
"""

result = extract_entities(text)
print("\nРезультат:")
for key, value in result.items():
    if value:
        print(f"  {key}: {value}")