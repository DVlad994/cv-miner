import json
import re
import pandas as pd


IT_POS_KEYWORDS = [
    "разработчик", "developer", "программист", "software engineer",
    "devops", "data scientist", "data engineer", "data analyst",
    "qa engineer", "qa automation", "тестировщик", "frontend",
    "backend", "fullstack", "machine learning", "ml engineer",
    "ios developer", "android developer", "системный аналитик",
    "team lead", "tech lead", "архитектор по", "architect",
    "веб-разработчик", "мобильный разработчик", "биг дата",
    "big data", "etl разработчик", "bi аналитик",
    "специалист по кибербезопасности", "пентестер",
]

IT_STOP_POSITIONS = [
    "инженер-электрик", "инженер-строитель", "инженер по эксплуатации",
    "инженер по охране труда", "инженер пто", "инженер-энергетик",
    "инженер-механик", "главный инженер", "инженер по ремонту",
    "инженер-технолог", "программист-электрик", "программист-строитель",
    "инженер программист электрик", "электрик", "строитель",
]


class ResumeDatasetGenerator:

    def __init__(self, csv_path="train.csv", output_path="resume_dataset.json"):
        self.csv_path = csv_path
        self.output_path = output_path
        self.SKILL_LABEL = "SKILL"
        self.ORG_LABEL = "ORG"
        self.POS_LABEL = "POS"
        self.EDU_LABEL = "EDU"
        self.ACH_LABEL = "ACHIEVEMENT"

    def tokenize(self, text):
        text = str(text).replace("\n", " ").replace("\t", " ").replace("\\", " ")
        return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)

    def is_punctuation_token(self, token):
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

    @staticmethod
    def is_it_position(position):
        if pd.isna(position):
            return False
        pos = str(position).lower()
        for stop in IT_STOP_POSITIONS:
            if stop in pos:
                return False
        return any(kw in pos for kw in IT_POS_KEYWORDS)


    def safe_json_extract(self, raw_text, field_name):
        if pd.isna(raw_text):
            return []
        text = str(raw_text).replace('""', '"')
        pattern = rf'"{field_name}"\s*:\s*"([^"]+)"'
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return [m.strip() for m in matches if len(m.strip()) > 1]


    def parse_skills(self, raw_skills):
        if pd.isna(raw_skills):
            return []
        text = str(raw_skills).replace('""', '"')
        matches = re.findall(r'"([^"]+)"', text)
        return list(set(
            m.strip() for m in matches
            if len(m.strip()) > 1 and "type" not in m.lower() and "code" not in m.lower()
        ))


    def parse_organizations(self, raw_work):
        return self.safe_json_extract(raw_work, "companyName")

    def parse_education(self, raw_edu):
        return self.safe_json_extract(raw_edu, "instituteName")


    def parse_job_titles(self, raw_work):
        return (self.safe_json_extract(raw_work, "jobTitle"))


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
            r"\d+\s*k",
            r"\d+\s+тыс",
            r"\d+\s+млн",
            r"\d+\s+проект",
            r"\d+\s+клиент",
            r"\d+\s+сервер",
            r"\d+\s+пользовател"
        ]
        achievements = []
        for pattern in patterns:
            for match in re.findall(pattern, text):
                if isinstance(match, tuple):
                    match = " ".join(match)
                achievements.append(match)
        return list(set(achievements))


    def build_resume_text(self, row):
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


    def generate_dataset(self):
        print("Загрузка CSV")
        df = pd.read_csv(self.csv_path, sep="|", engine="python", encoding="utf-8", on_bad_lines="skip")
        print(f"Строк: {len(df)}")
        dataset = []

        for index, row in df.iterrows():
            try:
                position = row.get("positionName")
                if not self.is_it_position(position):
                    continue

                full_text = self.build_resume_text(row)
                if len(full_text.strip()) < 30:
                    continue

                tokens = self.tokenize(full_text)
                labels = ["O"] * len(tokens)

                if pd.notna(position):
                    labels = self.add_entity(labels, tokens, self.tokenize(position), self.POS_LABEL)

                hard_skills = self.parse_skills(row.get("hardSkills_cv"))
                for skill in hard_skills:
                    labels = self.add_entity(labels, tokens, self.tokenize(skill), self.SKILL_LABEL)

                soft_skills = self.parse_skills(row.get("softSkills_cv"))
                for skill in soft_skills:
                    labels = self.add_entity(labels, tokens, self.tokenize(skill), self.SKILL_LABEL)

                orgs = self.parse_organizations(row.get("workExperienceList"))
                for org in orgs:
                    labels = self.add_entity(labels, tokens, self.tokenize(org), self.ORG_LABEL)

                education = self.parse_education(row.get("educationList"))
                for edu in education:
                    labels = self.add_entity(labels, tokens, self.tokenize(edu), self.EDU_LABEL)

                achievements = self.extract_achievements(full_text)
                for ach in achievements:
                    labels = self.add_entity(labels, tokens, self.tokenize(ach), self.ACH_LABEL)

                final_tokens = []
                for token, label in zip(tokens, labels):
                    if token.strip() and not self.is_punctuation_token(token.strip()):
                        final_tokens.append([token, label])

                if len(final_tokens) > 10:
                    dataset.append({"tokens": final_tokens})

                if index % 100 == 0:
                    print(f"Обработано {index}, в датасете: {len(dataset)}")

            except Exception as e:
                print(f"Ошибка в строке {index}: {e}")

        print(f"Сохранение: {self.output_path}")
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"Файл сохранён, записей: {len(dataset)}")


if __name__ == "__main__":
    generator = ResumeDatasetGenerator(csv_path="train.csv", output_path="resume_dataset.json")
    generator.generate_dataset()