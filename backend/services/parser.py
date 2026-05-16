import os
import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure, LTRect
from docx import Document
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path


def text_extraction(element) -> tuple:
    """Извлекает текст из текстового контейнера pdf"""
    line_text = element.get_text()
    line_formats = []

    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            for character in text_line:
                if isinstance(character, LTChar):
                    line_formats.append(character.fontname)
                    line_formats.append(character.size)

    format_per_line = list(set(line_formats))
    return line_text, format_per_line


def crop_image(element, page_obj):
    """вырезает изображение по координатам и распознаёт текст с помощью OCR"""
    [image_left, image_top, image_right, image_bottom] = [
        element.x0, element.y0, element.x1, element.y1
    ]
    page_obj.mediabox.lower_left = (image_left, image_bottom)
    page_obj.mediabox.upper_right = (image_right, image_top)

    cropped_pdf_writer = PyPDF2.PdfWriter()
    cropped_pdf_writer.add_page(page_obj)

    with open('cropped_image.pdf', 'wb') as f:
        cropped_pdf_writer.write(f)


def convert_to_images(input_file: str) -> str:
    """Конвертирует pdf в изображение для OCR"""
    images = convert_from_path(input_file)
    image = images[0]
    output_file = "PDF_image.png"
    image.save(output_file, "PNG")
    return output_file


def image_to_text(image_path: str) -> str:
    """Извлекает текст из изображения через tesseract"""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='rus+eng')
    return text.strip()



def extract_table(pdf_path: str, page_num: int, table_num: int) -> list:
    """Извлекает таблицу из pdf через pdfplumber, возвращает эту таблицу"""
    pdf = pdfplumber.open(pdf_path)
    table_page = pdf.pages[page_num]
    tables = table_page.extract_tables()
    pdf.close()
    if table_num < len(tables):
        return tables[table_num]
    return []


def table_converter(table: list) -> str:
    """преобразует таблицу в форматированную строку вида | ячейка | ячейка |"""
    table_string = ''
    for row in table:
        cleaned_row = [
            item.replace('\n', ' ') if item is not None else 'None'
            for item in row
        ]
        table_string += '|' + '|'.join(cleaned_row) + '|' + '\n'
    return table_string.strip()


def extract_text_from_pdf(filepath: str) -> dict:
    """
    Главная функция обработки pdf файлов
    :param filepath:
    :return: {
        'Page_0': [
            page_text,        # текст из текстовых блоков
            line_format,      # форматы текста
            text_from_images, # текст из изображений (OCR)
            text_from_tables, # текст из таблиц
            page_content      # полный текст страницы в порядке чтения
        ],
        ...
    }
    """
    pdf_file_obj = open(filepath, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
    text_per_page = {}

    for page_num, page in enumerate(extract_pages(filepath)):
        page_obj = pdf_reader.pages[page_num]

        page_text = []
        line_format = []
        text_from_images = []
        text_from_tables = []
        page_content = []

        table_num = 0
        first_element = True
        table_extraction_flag = False

        pdf_plumber = pdfplumber.open(filepath)
        page_tables = pdf_plumber.pages[page_num]
        tables = page_tables.find_tables()
        pdf_plumber.close()

        page_elements = [(element.y1, element) for element in page.objs]
        page_elements.sort(key=lambda a: a[0], reverse=True)

        for i, component in enumerate(page_elements):
            element = component[1]

            # текстовый блок pdf
            if isinstance(element, LTTextContainer):
                if not table_extraction_flag:
                    line_text, format_per_line = text_extraction(element)
                    page_text.append(line_text)
                    line_format.append(format_per_line)
                    page_content.append(line_text)

            # изображение
            if isinstance(element, LTFigure):
                try:
                    crop_image(element, page_obj)
                    image_file = convert_to_images('cropped_image.pdf')
                    image_text = image_to_text(image_file)
                    text_from_images.append(image_text)
                    page_content.append(image_text)
                    page_text.append('')
                    line_format.append('')
                except Exception:
                    pass

            # таблица
            if isinstance(element, LTRect):
                if first_element and (table_num + 1) <= len(tables):
                    lower_side = page.bbox[3] - tables[table_num].bbox[3]
                    upper_side = element.y1
                    table = extract_table(filepath, page_num, table_num)
                    if table:
                        table_string = table_converter(table)
                        text_from_tables.append(table_string)
                        page_content.append(table_string)
                    table_extraction_flag = True
                    first_element = False
                    page_text.append('')
                    line_format.append('')

                # Проверяем, чтоб не выйти за границы таблицы
                if element.y0 >= lower_side and element.y1 <= upper_side:
                    pass
                elif not isinstance(page_elements[i + 1][1], LTRect):
                    table_extraction_flag = False
                    first_element = True
                    table_num += 1

        dct_key = f'Page_{page_num}'
        text_per_page[dct_key] = [
            page_text,
            line_format,
            text_from_images,
            text_from_tables,
            page_content
        ]

    pdf_file_obj.close()

    for tmp_file in ['cropped_image.pdf', 'PDF_image.png']:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

    return text_per_page


def extract_text_from_docx(filepath: str) -> str:
    """Извлечение текста из word файлов"""
    text = ""
    doc = Document(filepath)
    for para in doc.paragraphs:
        if para.text:
            text += para.text + "\n"
    return text.strip()


def extract_text(filepath: str) -> dict:
    """определяет тип файла и извлекает текст"""
    ext = filepath.rsplit('.', 1)[-1].lower()

    try:
        if ext == 'pdf':
            result = extract_text_from_pdf(filepath)
            full_text = ""
            for page_key in sorted(result.keys()):
                page_content = result[page_key][4]
                full_text += "\n".join(page_content) + "\n"
            return {"success": True, "text": full_text.strip()}

        elif ext in ('docx', 'doc'):
            text = extract_text_from_docx(filepath)

        elif ext in ('png', 'jpg', 'jpeg'):
            text = image_to_text(filepath)

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