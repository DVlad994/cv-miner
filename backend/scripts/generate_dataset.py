import json
import random
import uuid
import re

NUM_RESUMES = 1000
OUTPUT_PATH = "resume_dataset.json"

FIRST_NAMES_MALE = [
    "Александр", "Михаил", "Максим", "Артём", "Даниил", "Иван", "Дмитрий",
    "Кирилл", "Никита", "Егор", "Андрей", "Илья", "Алексей", "Сергей",
    "Павел", "Владимир", "Роман", "Денис", "Антон", "Николай"
]

FIRST_NAMES_FEMALE = [
    "Анастасия", "Елена", "Ольга", "Наталья", "Екатерина", "Мария", "Анна",
    "Дарья", "Ксения", "Татьяна", "Юлия", "Александра", "София", "Виктория",
    "Полина", "Алёна", "Валерия", "Светлана", "Маргарита", "Людмила"
]

LAST_NAMES_MALE = [
    "Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров",
    "Соколов", "Михайлов", "Новиков", "Фёдоров", "Морозов", "Волков",
    "Алексеев", "Лебедев", "Семёнов", "Егоров", "Павлов", "Козлов"
]

LAST_NAMES_FEMALE = [
    "Иванова", "Смирнова", "Кузнецова", "Попова", "Васильева", "Петрова",
    "Соколова", "Михайлова", "Новикова", "Фёдорова", "Морозова", "Волкова",
    "Алексеева", "Лебедева", "Семёнова", "Егорова", "Павлова", "Козлова"
]

SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "C#", "C++", "PHP", "Ruby", "Kotlin",
    "Django", "FastAPI", "Flask", "React", "Vue.js", "Angular", "Next.js", "Spring",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "ClickHouse",
    "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitLab CI/CD",
    "Git", "Linux", "Nginx", "Bash", "REST API", "GraphQL", "gRPC",
    "SQL", "Pandas", "NumPy", "PyTorch", "TensorFlow", "Scikit-learn",
    "AWS", "Google Cloud", "Azure", "Yandex Cloud",
    "RabbitMQ", "Apache Kafka", "Celery", "Scrapy", "pytest",
    "Agile", "Scrum", "Jira", "Confluence", "Figma",
    "Администрирование СУБД", "Управление базами данных", "Проектирование API",
    "Микросервисная архитектура", "Юнит-тестирование", "Код-ревью",
    "Оптимизация запросов", "Системное администрирование", "DevOps практики",
    "Машинное обучение", "Глубокое обучение", "ETL-процессы",
    "Визуализация данных", "Бизнес-аналитика", "Управление проектами"
]

POSITIONS = [
    "Python-разработчик", "Senior Python Developer", "Middle Python Developer",
    "Junior Python Developer", "Backend-разработчик", "Fullstack-разработчик",
    "Frontend-разработчик", "Java-разработчик", "Go-разработчик",
    "DevOps-инженер", "SRE-инженер", "QA-инженер", "Senior QA", "Automation QA",
    "Data Scientist", "Data Analyst", "ML-инженер", "Data Engineer",
    "BI-аналитик", "ETL-разработчик", "Team Lead", "Технический директор",
    "CTO", "Архитектор решений", "Project Manager", "Product Manager",
    "Scrum Master", "Системный администратор", "Администратор баз данных"
]

COMPANIES = [
    "Яндекс", "Сбер", "VK", "Ozon", "Wildberries", "Тинькофф",
    "МТС", "Билайн", "Ростелеком", "МегаФон", "Альфа-Банк", "ВТБ",
    "Лаборатория Касперского", "Positive Technologies", "Avito",
    "2ГИС", "Skyeng", "HeadHunter", "Ostrovok.ru", "ЦИАН",
    "EPAM", "Luxoft", "Softline", "ЛАНИТ", "КРОК",
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix"
]

UNIVERSITIES = [
    "МГУ им. Ломоносова", "МФТИ", "ВШЭ", "МГТУ им. Баумана",
    "СПбГУ", "ИТМО", "МИФИ", "РАНХиГС", "УрФУ", "НГУ",
    "ТГУ", "ТПУ", "КФУ", "СФУ", "ДВФУ", "МИСиС",
    "МАИ", "МЭИ", "РЭУ им. Плеханова", "Финансовый университет"
]

SPECIALTIES = [
    "Информатика и вычислительная техника",
    "Программная инженерия",
    "Прикладная математика и информатика",
    "Системный анализ и управление",
    "Информационные системы и технологии",
    "Математическое обеспечение и администрирование информационных систем",
    "Информационная безопасность",
    "Бизнес-информатика",
    "Прикладная информатика",
    "Электроника и наноэлектроника"
]

CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
    "Казань", "Нижний Новгород", "Челябинск", "Краснодар", "Томск", "Сочи"
]

MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def generate_resume():
    gender = random.choice(["male", "female"])

    if gender == "male":
        first_name = random.choice(FIRST_NAMES_MALE)
        last_name = random.choice(LAST_NAMES_MALE)
    else:
        first_name = random.choice(FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES_FEMALE)

    full_name = f"{first_name} {last_name}"
    if random.random() > 0.7:
        middle_names = ["Александрович", "Михайлович", "Сергеевич", "Андреевич",
                       "Александровна", "Михайловна", "Сергеевна", "Андреевна"]
        full_name = f"{first_name} {random.choice(middle_names)} {last_name}"

    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
    phone = f"+79{random.randint(10,99)}{random.randint(100,999)}{random.randint(10,99)}{random.randint(10,99)}"
    city = random.choice(CITIES)

    num_skills = random.randint(5, 12)
    selected_skills = random.sample(SKILLS, num_skills)

    jobs = []
    num_jobs = random.randint(1, 3)
    current_year = 2024
    start_year = current_year - random.randint(3, 10)

    for job_num in range(num_jobs):
        company = random.choice(COMPANIES)
        position = random.choice(POSITIONS)
        job_start = start_year
        job_end = start_year + random.randint(1, 4)
        if job_num == num_jobs - 1:
            job_end_str = "настоящее время"
        else:
            job_end_str = str(job_end)
        start_year = int(job_end) + random.randint(0, 1) if job_end_str != "настоящее время" else current_year + 1

        duty_templates = [
            "Разработка и поддержка backend-сервисов",
            "Проектирование REST API",
            "Оптимизация запросов к БД",
            "Написание unit-тестов",
            "Участие в код-ревью",
            "Менторство junior-разработчиков",
            "Внедрение CI/CD",
            "Контейнеризация приложений",
            "Настройка мониторинга",
            "Рефакторинг легаси-кода",
            "Интеграция с внешними API",
            "Разработка микросервисов",
            "Документирование API",
            "Проведение code review",
        ]
        duties = random.sample(duty_templates, random.randint(2, 4))

        jobs.append({
            "start": str(job_start),
            "end": job_end_str,
            "company": company,
            "position": position,
            "duties": duties
        })

    university = random.choice(UNIVERSITIES)
    degree = random.choice(["Бакалавр", "Магистр"])
    specialty = random.choice(SPECIALTIES)
    edu_start = current_year - random.randint(8, 15)
    edu_end = edu_start + random.randint(4, 6)

    eng_level = random.choice(["A1", "A2", "B1", "B2", "C1"])

    resume = f"{full_name}\n\n"
    resume += "Контакты:\n"
    resume += f"Email: {email}\n"
    resume += f"Телефон: {phone}\n"
    resume += f"Город: {city}\n\n"
    resume += "Навыки:\n"
    for skill in selected_skills:
        resume += f"• {skill}\n"
    resume += "\nОпыт работы:\n\n"

    for job in jobs:
        resume += f"{job['start']} — {job['end']}\n"
        resume += f"{job['position']}, {job['company']}\n"
        for duty in job['duties']:
            resume += f"• {duty}\n"
        resume += "\n"

    resume += "Образование:\n"
    resume += f"{edu_start}-{edu_end}\n"
    resume += f"{university}, {degree}\n"
    resume += f"{specialty}\n\n"
    resume += "Иностранные языки:\n"
    resume += f"Английский — {eng_level}"

    return resume

def clean_token(token: str) -> str:
    """
    Удаление пунктуации, из-за которой ломались токены вроде Vue.js, Node.js, C++
    """
    return re.sub(
        r'^[^\w+#.\-/—]+|[^\w+#.\-/—]+$',
        '',
        token,
        flags=re.UNICODE
    )

def find_entity(words, labels, entities, label_prefix):
    lowered = [w.lower() for w in words]

    for entity in sorted(entities, key=len, reverse=True):
        entity_words = [clean_token(w).lower() for w in entity.split()]

        for i in range(len(lowered)):
            matched = True

            for j in range(len(entity_words)):
                if i + j >= len(lowered):
                    matched = False
                    break

                if lowered[i + j] != entity_words[j]:
                    matched = False
                    break

            if matched:
                for j in range(len(entity_words)):
                    labels[i + j] = f"B-{label_prefix}" if j == 0 else f"I-{label_prefix}"

def label_line(line, section):
    line_stripped = line.strip()

    if not line_stripped:
        return [], []

    words = line_stripped.split()
    clean_words = [clean_token(w) for w in words]
    labels = ["O"] * len(clean_words)

    if section == "name":
        for i, token in enumerate(clean_words):
            if token in FIRST_NAMES_MALE + FIRST_NAMES_FEMALE:
                labels[i] = "B-NAME"
            elif token in LAST_NAMES_MALE + LAST_NAMES_FEMALE:
                labels[i] = "I-NAME"
            elif token.endswith(("вич", "вна")):
                labels[i] = "I-NAME"

    elif section == "contacts":
        for i, token in enumerate(clean_words):
            if "@" in token:
                labels[i] = "B-EMAIL"
            elif re.match(r'^\+?\d[\d\-\(\)\s]{9,}$', token):
                labels[i] = "B-PHONE"

        find_entity(clean_words, labels, CITIES, "LOC")

    elif section == "skills":
        full_line = line_stripped.replace("•", "").strip()

        for skill in sorted(SKILLS, key=len, reverse=True):
            if skill.lower() == full_line.lower():
                skill_words = [clean_token(w) for w in skill.split()]
                start_idx = 1 if words[0] == "•" else 0

                for j in range(len(skill_words)):
                    idx = start_idx + j

                    if idx < len(labels):
                        labels[idx] = "B-SKILL" if j == 0 else "I-SKILL"

    elif section == "experience_date":
        for i, token in enumerate(clean_words):
            if re.match(r'^\d{4}$', token):
                labels[i] = "B-DATE"
            elif re.match(r'^\d{4}[-–]\d{4}$', token):
                labels[i] = "B-DATE"
            elif token.lower() == "настоящее":
                labels[i] = "B-DATE"
            elif token.lower() == "время":
                if i > 0 and labels[i - 1] == "B-DATE":
                    labels[i] = "I-DATE"

    elif section == "experience_position":
        find_entity(clean_words, labels, POSITIONS, "POS")
        find_entity(clean_words, labels, COMPANIES, "ORG")

    elif section == "education":
        for i, token in enumerate(clean_words):
            if re.match(r'^\d{4}[-–]\d{4}$', token):
                labels[i] = "B-DATE"

        find_entity(clean_words, labels, UNIVERSITIES, "EDU")
        find_entity(clean_words, labels, SPECIALTIES, "EDU")

    return clean_words, labels

def tokenize_and_label(text):
    tokens = []
    labels = []

    lines = text.split("\n")
    current_section = "name"

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if not line_stripped:
            continue

        if line_lower.startswith("контакты"):
            current_section = "contacts"

        elif line_lower.startswith("навыки"):
            current_section = "skills"

        elif line_lower.startswith("опыт работы"):
            current_section = "experience"

        elif line_lower.startswith("образование"):
            current_section = "education"

        elif line_lower.startswith("иностранные"):
            current_section = "languages"

        section_for_line = current_section

        if current_section == "experience":
            if re.match(r'^\d{4}', line_stripped):
                section_for_line = "experience_date"
            elif line_stripped.startswith("•"):
                section_for_line = "experience_duty"
            else:
                section_for_line = "experience_position"

        words, line_labels = label_line(line, section_for_line)

        for w, l in zip(words, line_labels):
            if not w:
                continue

            tokens.append(w)
            labels.append(l)

    return list(zip(tokens, labels))


def generate_dataset(num_resumes):
    dataset = []
    for i in range(num_resumes):
        if (i + 1) % 100 == 0:
            print(f"Сгенерировано {i + 1} резюме...")
        resume_text = generate_resume()
        labeled = tokenize_and_label(resume_text)
        dataset.append({
            "id": str(uuid.uuid4()),
            "text": resume_text,
            "tokens": labeled
        })
    return dataset


if __name__ == "__main__":
    print(f"Генерация {NUM_RESUMES} синтетических резюме...")
    dataset = generate_dataset(NUM_RESUMES)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Датасет сохранён в {OUTPUT_PATH}")
    print(f"Всего резюме: {len(dataset)}")