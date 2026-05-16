import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from services.parser import extract_text

api_bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api_bp.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'file' not in request.files:
        return jsonify({"error": "Файл обязателен"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Неподдерживаемый формат. Допустимые: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    print(f"Загружен: {file.filename}")

    parse_result = extract_text(filepath)

    if not parse_result['success']:
        print(f"ОШИБКА: {parse_result['error']}")
        return jsonify({"error": parse_result['error']}), 400

    resume_text = parse_result['text']

    return jsonify({
        "analysis_id": str(uuid.uuid4()),
        "filename": file.filename,
        "text_length": len(resume_text),
        "full_text": resume_text
    })


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})