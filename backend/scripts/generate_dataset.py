import json
import random
import re

import pandas as pd

IT_POS_KEYWORDS = [
    "разработчик", "developer", "программист", "software engineer",
    "devops", "data scientist", "data engineer", "data analyst",
    "qa engineer", "qa automation", "тестировщик", "frontend",
    "backend", "fullstack", "machine learning", "ml engineer",
    "ios developer", "android developer", "системный аналитик",
    "team lead", "tech lead", "веб-разработчик", "big data",
    "etl разработчик", "bi аналитик", "кибербезопасности", "пентестер",
]

TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "angular",
    "vue", "django", "fastapi", "flask", "docker", "kubernetes", "git",
    "sql", "postgresql", "mysql", "mongodb", "redis", "linux", "aws",
    "azure", "c++", "c#", "php", "ruby", "go", "rust", "node.js",
    "spring", "flutter", "swift", "kotlin", "html5", "css3",
    "rest api", "graphql", "pandas", "numpy", "tensorflow", "pytorch",
    "scikit-learn", "rabbitmq", "kafka", "elasticsearch", "nginx",
    "bash", "terraform", "ansible", "jenkins", "gitlab", "ci/cd",
    "prometheus", "grafana", "clickhouse", "helm", "argocd",
}

SYNTH_SKILLS = sorted(TECH_SKILLS)
SYNTH_POSITIONS = [
    "Python-разработчик", "Senior Python Developer", "Middle Python Developer",
    "Junior Python Developer", "Backend-разработчик", "Fullstack-разработчик",
    "Frontend-разработчик", "Java-разработчик", "Go-разработчик",
    "DevOps-инженер", "SRE-инженер", "QA-инженер", "Data Scientist",
    "Data Analyst", "ML-инженер", "Data Engineer", "Team Lead",
    "Технический директор", "Архитектор решений", "System Administrator",
]
SYNTH_COMPANIES = [
    "Яндекс", "Сбер", "VK", "Ozon", "Wildberries", "Тинькофф", "Avito",
    "Сбер", "АльфаБанк", "2ГИС", "ВТБ", "ЦентроБанк", "МТС", "Т-Банк",
    "HeadHunter", "EPAM", "Банк", "", "Microsoft", "ООО", "Фриланс"
]
SYNTH_UNIVERSITIES = [
    "МГУ им. Ломоносова", "МФТИ", "ВШЭ", "МГТУ им. Баумана",
    "СПбГУ", "СПбГТУ", "ИТМО", "МИФИ", "УрФУ", "НГУ", "ТГУ", "МИСИС",
    "НГУ", "НГТУ", "АГУ", "АлтГТУ",
]
SYNTH_CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Казань", "Томск", "Краснодар", "Сочи"]


class ResumeDatasetGenerator:
    """
    Половина датасета будет реальная, половина синтетическая,
    иначе нейросеть просто не может запомнить некоторые навыки, которые встречаются редко в реальных резюме
    Kubernetes, Docker, FastAPI и какие-то прочие фреймворки
    """
    def __init__(self, csv_path="train.csv", output_path="resume_dataset.json",
                 num_synthetic=1140):
        # 1140 синтетических резюме = кол-ву реальных, смешаем поровну
        self.csv_path = csv_path
        self.output_path = output_path
        self.num_synthetic = num_synthetic
        self.SKILL_LABEL = "SKILL"
        self.ORG_LABEL = "ORG"
        self.POS_LABEL = "POS"
        self.EDU_LABEL = "EDU"
        self.ACH_LABEL = "ACHIEVEMENT"

    def tokenize(self, text):
        text = str(text).replace("\n", " ").replace("\t", " ").replace("\\", " ")
        return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)

    def is_punctuation_token(self, token):
        """
        Является ли знаком пунктуации
        :param token:
        :return:
        """
        return len(token) == 1 and token in ",-.:;!/\\"

    def add_entity(self, labels, tokens, entity_tokens, label_name):
        if not entity_tokens:
            return labels
        entity_lower = [x.lower() for x in entity_tokens]
        for i in range(len(tokens)):
            chunk = tokens[i:i + len(entity_tokens)]
            if [x.lower() for x in chunk] == entity_lower:
                labels[i] = f"B-{label_name}"
                for j in range(1, len(entity_tokens)):
                    if i + j < len(labels):
                        labels[i + j] = f"I-{label_name}"
        return labels

    def is_it_professional(self, row):
        """
        it - IT
        :param row:
        :return: является ли IT-специалистом или нет
        """
        work = row.get("workExperienceList")
        if pd.notna(work):
            try:
                works = json.loads(str(work).replace('""', '"'))
                for w in works:
                    title = w.get("jobTitle", "").lower()
                    if any(kw in title for kw in IT_POS_KEYWORDS):
                        return True
            except Exception:
                pass
        skills = row.get("hardSkills_cv")
        if pd.notna(skills):
            try:
                skills_list = json.loads(str(skills).replace('""', '"'))
                for s in skills_list:
                    if isinstance(s, str) and s.lower() in TECH_SKILLS:
                        return True
            except Exception:
                pass
        return False

    def extract_tech_from_text(self, text):
        """
        Вытянуть технические навыки из резюме
        :param text:
        :return: список навыков
        """
        found = []
        text_lower = text.lower()
        for tech in sorted(TECH_SKILLS, key=len, reverse=True):
            if tech in text_lower and tech not in found:
                found.append(tech)
        return found


    def safe_json_extract(self, raw_text, field_name):
        if pd.isna(raw_text):
            return []
        text = str(raw_text).replace('""', '"')
        pattern = rf'"{field_name}"\s*:\s*"([^"]+)"'
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return [m.strip() for m in matches if len(m.strip()) > 1]

    def parse_skills(self, raw_skills):
        """
        Парсинг навыков
        :param raw_skills:
        :return: список навыков
        """
        if pd.isna(raw_skills):
            return []
        text = str(raw_skills).replace('""', '"')
        matches = re.findall(r'"([^"]+)"', text)
        return list(set(m.strip() for m in matches if len(m.strip()) > 1
                       and "type" not in m.lower() and "code" not in m.lower()))

    def parse_organizations(self, raw_work):
        return self.safe_json_extract(raw_work, "companyName")

    def parse_education(self, raw_edu):
        return self.safe_json_extract(raw_edu, "instituteName")

    def parse_job_titles(self, raw_work):
        return self.safe_json_extract(raw_work, "jobTitle")

    def extract_demands(self, raw_work):
        return self.safe_json_extract(raw_work, "demands")

    def extract_achievements(self, text):
        text = str(text).lower()
        patterns = [
            r"\d+\s*%",
            r"увеличил[аи]?\s.*?\d+\s*%",
            r"снизил[аи]?\s.*?\d+\s*%",
            r"оптимизировал[аи]?\s.*?\d+\s*%",
            r"ускорил[аи]?\s.*?\d+\s*%",
            r"повысил[аи]?\s.*?\d+\s*%",
            r"с\s+\d+\s+до\s+\d+",
            r"\d+\s+человек",
            r"команд[аы]\s+из\s+\d+",
            r"\d+\s+раз",
        ]
        achievements = []
        for pattern in patterns:
            for match in re.findall(pattern, text):
                if isinstance(match, tuple):
                    match = " ".join(match)
                achievements.append(match)
        return list(set(achievements))

    def extract_real_cv(self, row):
        """
        Получаем данные из реальных, отфильтрованных резюме
        :param row:
        :return:
        """
        parts = []
        position = row.get("positionName", "")
        if pd.notna(position):
            parts.append(f"Должность: {position}")
        hard_skills = self.parse_skills(row.get("hardSkills_cv"))
        if hard_skills:
            parts.append("Навыки: " + ", ".join(hard_skills))
        soft_skills = self.parse_skills(row.get("softSkills_cv"))
        if soft_skills:
            parts.append("Soft skills: " + ", ".join(soft_skills))
        orgs = self.parse_organizations(row.get("workExperienceList"))
        if orgs:
            parts.append("Компании: " + ", ".join(orgs))
        jobs = self.parse_job_titles(row.get("workExperienceList"))
        if jobs:
            parts.append("Опыт работы: " + ", ".join(jobs))
        demands = self.extract_demands(row.get("workExperienceList"))
        if demands:
            parts.append("Обязанности: " + " ".join(demands))
        education = self.parse_education(row.get("educationList"))
        if education:
            parts.append("Образование: " + ", ".join(education))
        return "\n".join(parts)


    def generate_synthetic_cv(self):
        """
        Генерируем синтетические резюме (примерно 50% от общего числа)
        Нейросеть не может обучиться нормально на реальных резюме,
        например, навык Kubernetes встречается 8 раз из 2500 резюме, и нейросеть воспринимает его как шум
        :return: список синтетических резюме (рекомендуется от 500 до 2000)
        """
        position = random.choice(SYNTH_POSITIONS)
        company = random.choice(SYNTH_COMPANIES)
        university = random.choice(SYNTH_UNIVERSITIES)
        city = random.choice(SYNTH_CITIES)
        skills = random.sample(SYNTH_SKILLS, random.randint(5, 10))
        exp_years = random.randint(1, 10)
        text = f"Должность: {position}\n"
        text += f"Компании: {company}\n"
        text += f"Город: {city}\n"
        text += f"Опыт работы: {exp_years} лет\n"
        text += "Навыки: " + ", ".join(skills) + "\n"
        text += "Обязанности: Разработка и поддержка сервисов, работа с " + ", ".join(skills[:3]) + "\n"
        text += f"Образование: {university}\n"
        return text, skills, [company], [position], [university]


    def generate_dataset(self):
        dataset = []

        print("Загрузка CSV")
        df = pd.read_csv(self.csv_path, sep="|", engine="python", encoding="utf-8", on_bad_lines="skip")
        print(f"Строк: {len(df)}")

        real_count = 0
        for index, row in df.iterrows():
            try:
                if not self.is_it_professional(row):
                    continue
                full_text = self.extract_real_cv(row)
                if len(full_text.strip()) < 30:
                    continue
                tokens = self.tokenize(full_text)
                labels = ["O"] * len(tokens)

                position = row.get("positionName")
                if pd.notna(position):
                    labels = self.add_entity(labels, tokens, self.tokenize(position), self.POS_LABEL)

                for skill in self.parse_skills(row.get("hardSkills_cv")):
                    labels = self.add_entity(labels, tokens, self.tokenize(skill), self.SKILL_LABEL)
                for skill in self.parse_skills(row.get("softSkills_cv")):
                    labels = self.add_entity(labels, tokens, self.tokenize(skill), self.SKILL_LABEL)
                for skill in self.extract_tech_from_text(full_text):
                    labels = self.add_entity(labels, tokens, self.tokenize(skill), self.SKILL_LABEL)
                for org in self.parse_organizations(row.get("workExperienceList")):
                    labels = self.add_entity(labels, tokens, self.tokenize(org), self.ORG_LABEL)
                for edu in self.parse_education(row.get("educationList")):
                    labels = self.add_entity(labels, tokens, self.tokenize(edu), self.EDU_LABEL)
                for ach in self.extract_achievements(full_text):
                    labels = self.add_entity(labels, tokens, self.tokenize(ach), self.ACH_LABEL)

                final_tokens = [[t, l] for t, l in zip(tokens, labels)
                               if t.strip() and not self.is_punctuation_token(t.strip())]
                if len(final_tokens) > 10:
                    dataset.append({"tokens": final_tokens})
                    real_count += 1
            except Exception as e:
                print(f"Ошибка в строке {index}: {e}")

        print(f"Реальных резюме: {real_count}")

        print(f"Генерация {self.num_synthetic} синтетических резюме")
        for _ in range(self.num_synthetic):
            text, skills, orgs, positions, edus = self.generate_synthetic_cv()
            tokens = self.tokenize(text)
            labels = ["O"] * len(tokens)
            for skill in skills:
                labels = self.add_entity(labels, tokens, self.tokenize(skill), self.SKILL_LABEL)
            for org in orgs:
                labels = self.add_entity(labels, tokens, self.tokenize(org), self.ORG_LABEL)
            for pos in positions:
                labels = self.add_entity(labels, tokens, self.tokenize(pos), self.POS_LABEL)
            for edu in edus:
                labels = self.add_entity(labels, tokens, self.tokenize(edu), self.EDU_LABEL)
            final_tokens = [[t, l] for t, l in zip(tokens, labels)
                           if t.strip() and not self.is_punctuation_token(t.strip())]
            if len(final_tokens) > 10:
                dataset.append({"tokens": final_tokens})

        random.shuffle(dataset)

        print(f"Всего записей датасета: {len(dataset)}\n"
            f"Первые 5 записей полученного датасета:\n")
        for i in range(5):
            print(dataset[i])


        print(f"Сохранение: {self.output_path}")
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"Файл сохранён, записей: {len(dataset)}")


if __name__ == "__main__":
    generator = ResumeDatasetGenerator(csv_path="train.csv", output_path="resume_dataset.json", num_synthetic=1140)
    generator.generate_dataset()
