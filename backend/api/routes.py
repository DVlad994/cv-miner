import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from services.parser import extract_text
from services.analyzer import analyze_resume_text, rank_resumes
from services import database as db

api_bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

# Celery подключаем мягко: если брокер/пакет недоступны, система продолжает
# работать в синхронном режиме, а async-эндпоинты возвращают понятную ошибку
try:
    from services import tasks as celery_tasks
    CELERY_AVAILABLE = True
except Exception:
    celery_tasks = None
    CELERY_AVAILABLE = False


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_file(file):
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath


def _resolve_vacancy():
    vacancy_text = request.form.get('vacancy_text', '').strip()
    vacancy_id = request.form.get('vacancy_id', type=int)
    vacancy_title = None
    if vacancy_id:
        vac = db.get_vacancy(vacancy_id)
        if not vac:
            return None, None, None, (jsonify({"error": "Вакансия не найдена"}), 404)
        vacancy_text = vac['requirements']
        vacancy_title = vac['title']
    if not vacancy_text:
        return None, None, None, (jsonify({"error": "Текст вакансии обязателен"}), 400)
    return vacancy_text, vacancy_id, vacancy_title, None


def _save_and_extract(file):
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    parse_result = extract_text(filepath)
    if not parse_result['success']:
        return None, parse_result['error']
    return parse_result['text'], None


@api_bp.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'file' not in request.files:
        return jsonify({"error": "Файл обязателен"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Неподдерживаемый формат. Допустимые: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    vacancy_text = request.form.get('vacancy_text', '').strip()
    vacancy_id = request.form.get('vacancy_id', type=int)
    vacancy_title = None
    if vacancy_id:
        vac = db.get_vacancy(vacancy_id)
        if not vac:
            return jsonify({"error": "Вакансия не найдена"}), 404
        vacancy_text = vac['requirements']
        vacancy_title = vac['title']
    if not vacancy_text:
        return jsonify({"error": "Текст вакансии обязателен"}), 400

    resume_text, err = _save_and_extract(file)
    if err:
        return jsonify({"error": err}), 400

    analysis = analyze_resume_text(resume_text, vacancy_text)
    analysis_id = str(uuid.uuid4())

    db.save_analysis(
        analysis_id=analysis_id,
        filename=file.filename,
        vacancy_id=vacancy_id,
        vacancy_title=vacancy_title,
        candidate=analysis["candidate"],
        profile=analysis["profile"],
        matching=analysis["matching_result"],
    )

    return jsonify({
        "analysis_id": analysis_id,
        "filename": file.filename,
        "text_length": len(resume_text),
        "full_text": resume_text,
        "candidate": analysis["candidate"],
        "profile": analysis["profile"],
        "matching_result": analysis["matching_result"],
    })


@api_bp.route('/rank', methods=['POST'])
def rank_candidates():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "Необходимо загрузить хотя бы один файл"}), 400

    vacancy_text = request.form.get('vacancy_text', '').strip()
    vacancy_id = request.form.get('vacancy_id', type=int)
    vacancy_title = None
    if vacancy_id:
        vac = db.get_vacancy(vacancy_id)
        if not vac:
            return jsonify({"error": "Вакансия не найдена"}), 404
        vacancy_text = vac['requirements']
        vacancy_title = vac['title']
    if not vacancy_text:
        return jsonify({"error": "Текст вакансии обязателен"}), 400

    resumes = []
    skipped = []
    for file in files:
        if file.filename == '' or not allowed_file(file.filename):
            skipped.append(file.filename or '(без имени)')
            continue
        resume_text, err = _save_and_extract(file)
        if err:
            skipped.append(file.filename)
            continue
        resumes.append({"filename": file.filename, "text": resume_text})

    if not resumes:
        return jsonify({"error": "Не удалось обработать ни одного файла", "skipped": skipped}), 400

    ranking = rank_resumes(resumes, vacancy_text)

    for r in ranking:
        db.save_analysis(
            analysis_id=str(uuid.uuid4()),
            filename=r["filename"],
            vacancy_id=vacancy_id,
            vacancy_title=vacancy_title,
            candidate=r["candidate"],
            profile=r["profile"],
            matching=r["matching_result"],
        )

    # наружу отдаём только то, что нужно таблице рейтинга - без тяжелого текста резюме
    compact = [{
        "rank": r["rank"],
        "filename": r["filename"],
        "candidate_name": r["candidate_name"],
        "total_score": r["total_score"],
        "skills_score": r["skills_score"],
        "level": r["level"],
        "domain": r["domain"],
        "matched": r["matched"],
        "partial": r["partial"],
        "missing": r["missing"],
        "explanation": r["matching_result"].get("explanation"),
    } for r in ranking]

    return jsonify({
        "vacancy_title": vacancy_title,
        "count": len(compact),
        "skipped": skipped,
        "ranking": compact,
    })



@api_bp.route('/vacancies', methods=['GET'])
def get_vacancies():
    return jsonify(db.list_vacancies())


@api_bp.route('/vacancies', methods=['POST'])
def add_vacancy():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    requirements = (data.get('requirements') or '').strip()
    if not title or not requirements:
        return jsonify({"error": "Поля title и requirements обязательны"}), 400
    vac = db.create_vacancy(title, data.get('department', ''), requirements)
    return jsonify(vac), 201


@api_bp.route('/vacancies/<int:vacancy_id>', methods=['PUT'])
def edit_vacancy(vacancy_id):
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    requirements = (data.get('requirements') or '').strip()
    if not title or not requirements:
        return jsonify({"error": "Поля title и requirements обязательны"}), 400
    vac = db.update_vacancy(vacancy_id, title, data.get('department', ''), requirements)
    if not vac:
        return jsonify({"error": "Вакансия не найдена"}), 404
    return jsonify(vac)


@api_bp.route('/vacancies/<int:vacancy_id>', methods=['DELETE'])
def remove_vacancy(vacancy_id):
    if db.delete_vacancy(vacancy_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Вакансия не найдена"}), 404


# История прошлых анализов

@api_bp.route('/analyses', methods=['GET'])
def get_analyses():
    # vacancy_id опционально - если передан, показываем историю только по этой вакансии
    vacancy_id = request.args.get('vacancy_id', type=int)
    limit = request.args.get('limit', default=100, type=int)
    return jsonify(db.list_analyses(limit=limit, vacancy_id=vacancy_id))


@api_bp.route('/analyses/<analysis_id>', methods=['GET'])
def get_analysis_detail(analysis_id):
    # полная карточка по клику "Подробнее" в истории
    rec = db.get_analysis(analysis_id)
    if not rec:
        return jsonify({"error": "Анализ не найден"}), 404
    return jsonify(rec)


# Асинхронная обработка через Celery: тяжёлый анализ уходит в worker,
# клиент получает task_id и опрашивает /tasks/<id>

@api_bp.route('/analyze/async', methods=['POST'])
def analyze_async():
    if not CELERY_AVAILABLE:
        return jsonify({"error": "Асинхронный режим недоступен (нет брокера)"}), 503
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({"error": "Файл обязателен"}), 400
    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({"error": "Неподдерживаемый формат"}), 400

    vac_text, vac_id, vac_title, err = _resolve_vacancy()
    if err:
        return err

    filepath = _save_file(file)
    task = celery_tasks.analyze_resume_task.delay(
        filepath, file.filename, vac_text, vac_id, vac_title)
    # 202 Accepted задача принята, но ещё не выполнена
    return jsonify({"task_id": task.id, "status": "queued"}), 202


@api_bp.route('/rank/async', methods=['POST'])
def rank_async():
    if not CELERY_AVAILABLE:
        return jsonify({"error": "Асинхронный режим недоступен (нет брокера)"}), 503
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "Необходимо загрузить хотя бы один файл"}), 400

    vac_text, vac_id, vac_title, err = _resolve_vacancy()
    if err:
        return err

    saved = []
    for f in files:
        if f.filename and allowed_file(f.filename):
            saved.append({"filepath": _save_file(f), "original_name": f.filename})
    if not saved:
        return jsonify({"error": "Нет подходящих файлов"}), 400

    task = celery_tasks.rank_resumes_task.delay(saved, vac_text, vac_id, vac_title)
    return jsonify({"task_id": task.id, "status": "queued"}), 202


@api_bp.route('/tasks/<task_id>', methods=['GET'])
def task_status(task_id):
    """Статус фоновой задачи: PENDING / STARTED / SUCCESS / FAILURE"""
    if not CELERY_AVAILABLE:
        return jsonify({"error": "Асинхронный режим недоступен"}), 503
    res = celery_tasks.celery_app.AsyncResult(task_id)
    payload = {"task_id": task_id, "status": res.status}
    if res.successful():
        payload["result"] = res.result
    elif res.failed():
        payload["error"] = str(res.result)
    return jsonify(payload)


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "async": CELERY_AVAILABLE})
