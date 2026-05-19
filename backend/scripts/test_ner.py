from backend.services.analyzer import extract_entities, ner_model, NER_MODEL_PATH

print(f"Модель загружена: {ner_model is not None}")
print(f"Путь к модели: {NER_MODEL_PATH}")

# стандартное резюме, которое может быть обработано с помощью правил (regex)
text = """Артём Власов

tg: @artem_dev
для связи: artem.vlsv@protonmail.com

Живу в Казани

Чем занимался:

— собирал сервисы для обработки огромного количества логов
— поднимал контейнерную инфраструктуру
— автоматизировал выкладку релизов, ускорил на 50%
— писал внутренние инструменты для аналитиков
— занимался отказоустойчивостью, повысил на 40%
— ускорял тяжёлые SQL-запросы
— настраивал пайплайны доставки

Стек:

PyTorch
RabbitMQ
Grafana
Prometheus
ClickHouse
Go
Python
Helm
ArgoCD

Где работал:

2019 — 2021
занимался внутренней платформой обработки данных
Тинькофф

2021 — настоящее время
руковожу командой backend/platform engineering
Ozon Tech

Образование:

КФУ
Институт вычислительной математики и информационных технологий

Английский — Upper-Intermediate
"""

result = extract_entities(text)

print(result)
