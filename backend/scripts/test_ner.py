import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification
)
from transformers import pipeline

MODEL_PATH = "./rubert-ner-resume"

print("Загрузка модели...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)

device = 0 if torch.cuda.is_available() else -1

ner = pipeline(
    "token-classification",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple",
    device=device
)

# нестандартное резюме, нет прямого названия должности, редкие навыки
text = """
Артём Власов

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


entities = ner(text)
for entity in entities:
    print(f"{entity['word']} "f"-> {entity['entity_group']} "f"({round(entity['score'], 3)})")