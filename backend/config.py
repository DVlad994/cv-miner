import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    HOST = os.getenv('HOST', 'localhost')
    PORT = int(os.getenv('PORT', 8000))
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 МБ загружаемый файл
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')