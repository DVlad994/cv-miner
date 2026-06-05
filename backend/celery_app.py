import os
from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery("cvminer", broker=BROKER, backend=BACKEND)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,          # результаты живут час
    task_track_started=True,      # статус STARTED, а не только PENDING/SUCCESS
    worker_max_tasks_per_child=50,  # перезапуск воркера
)

# задачи лежат в отдельном модуле, импортируем чтобы Celery их зарегистрировал
celery_app.autodiscover_tasks(["services"])
