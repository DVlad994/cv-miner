from docx import Document
import pytesseract
from PIL import Image

# todo пока что не работает
def extract_text_from_pdf(filepath: str) -> str:
    """Извлечение текста из pdf файла"""
    return "Доделать потом"


def extract_text_from_docx(filepath: str) -> str:
    """Извлекаем текст из word файла"""
    text = ""
    doc = Document(filepath)
    for para in doc.paragraphs:
        if para.text:
            text += para.text + "\n"
    return text.strip()


def extract_text_from_image(filepath: str) -> str:
    """Извлекаем текст из изображения с помощью OCR
    (тестовая функция может не возвращать ожидаемый результат)"""
    image = Image.open(filepath)
    text = pytesseract.image_to_string(image, lang='rus+eng')
    return text.strip()


def extract_text(filepath: str) -> dict:
    """Извлекает тип файла и обрабатывает в дальнейшем"""
    ext = filepath.rsplit('.', 1)[-1].lower()

    try:
        if ext == 'pdf':
            text = extract_text_from_pdf(filepath)
        elif ext in ('docx', 'doc'):
            text = extract_text_from_docx(filepath)
        elif ext in ('png', 'jpg', 'jpeg'):
            text = extract_text_from_image(filepath)
        else:
            return {"success": False, "error": f"Неподдерживаемый формат: {ext}"}

        if not text:
            return {
                "success": False,
                "error": "Не удалось извлечь текст."
            }

        return {"success": True, "text": text}

    except Exception as e:
        return {"success": False, "error": f"Ошибка при извлечении текста: {str(e)}"}