from flask import Flask
from flask_cors import CORS
from config import Config
from api.routes import api_bp
from services import database as db

app = Flask(__name__)
app.config.from_object(Config)

# Настройка CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Создаём папку для загрузок и инициализируем БД при старте
import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_db()

# Регистрируем blueprint
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/')
def index():
    return {
        "service": "CV-Miner API",
        "version": "0.1.0",
        "status": "running"
    }


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )