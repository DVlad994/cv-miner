from backend.services.analyzer import extract_entities

text = """
Иван Сергеевич Петров

Email: ivan.petrov@gmail.com
Телефон: +79991234567
Город: Москва

Навыки:
Python
FastAPI
Docker
Kubernetes
PostgreSQL

Опыт работы:

2020 — настоящее время
Senior Python Developer, Яндекс

2018 — 2020
Backend-разработчик, VK

Образование:
МГУ им. Ломоносова
Прикладная информатика
"""

result = extract_entities(text)

print(result)