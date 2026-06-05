import uuid

from celery_app import celery_app
from services.parser import extract_text
from services.analyzer import analyze_resume_text, rank_resumes
from services import database as db


@celery_app.task(bind=True, name="services.tasks.analyze_resume_task")
def analyze_resume_task(self, filepath, original_name, vacancy_text,
                        vacancy_id, vacancy_title):
    """
    Фоновый анализ одного резюме: парсинг -> анализ -> сохранение в историю
    """
    parse = extract_text(filepath)
    if not parse["success"]:
        # Celery пометит задачу как FAILURE с этим текстом
        raise ValueError(parse["error"])

    resume_text = parse["text"]
    analysis = analyze_resume_text(resume_text, vacancy_text)
    analysis_id = str(uuid.uuid4())

    db.save_analysis(
        analysis_id=analysis_id,
        filename=original_name,
        vacancy_id=vacancy_id,
        vacancy_title=vacancy_title,
        candidate=analysis["candidate"],
        profile=analysis["profile"],
        matching=analysis["matching_result"],
    )

    return {
        "analysis_id": analysis_id,
        "filename": original_name,
        "text_length": len(resume_text),
        "full_text": resume_text,
        "candidate": analysis["candidate"],
        "profile": analysis["profile"],
        "matching_result": analysis["matching_result"],
    }


@celery_app.task(bind=True, name="services.tasks.rank_resumes_task")
def rank_resumes_task(self, files, vacancy_text, vacancy_id, vacancy_title):
    """
    Фоновое ранжирование пачки резюме по одной вакансии.
    files: список [{"filepath", "original_name"}].
    """
    resumes, skipped = [], []
    for f in files:
        parse = extract_text(f["filepath"])
        if not parse["success"]:
            skipped.append(f["original_name"])
            continue
        resumes.append({"filename": f["original_name"], "text": parse["text"]})

    if not resumes:
        raise ValueError("Не удалось обработать ни одного файла")

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

    compact = [{
        "rank": r["rank"], "filename": r["filename"],
        "candidate_name": r["candidate_name"], "total_score": r["total_score"],
        "skills_score": r["skills_score"], "level": r["level"], "domain": r["domain"],
        "matched": r["matched"], "partial": r["partial"], "missing": r["missing"],
        "explanation": r["matching_result"].get("explanation"),
    } for r in ranking]

    return {"vacancy_title": vacancy_title, "count": len(compact),
            "skipped": skipped, "ranking": compact}
