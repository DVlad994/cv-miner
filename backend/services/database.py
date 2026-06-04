import os
import json
import sqlite3
import threading
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cvminer.db")

#сериализуем доступ
_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Создаём таблицы при первом запуске и подкидываем демо-вакансию,
    чтобы интерфейс не был пустым на свежей машине
    """
    with _lock, _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                department   TEXT DEFAULT '',
                requirements TEXT NOT NULL,
                created_at   TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id  TEXT UNIQUE NOT NULL,
                filename     TEXT,
                vacancy_id   INTEGER,
                vacancy_title TEXT,
                candidate_name TEXT,
                total_score  REAL,
                candidate    TEXT,
                profile      TEXT,
                matching     TEXT,
                created_at   TEXT NOT NULL,
                FOREIGN KEY (vacancy_id) REFERENCES vacancies(id) ON DELETE SET NULL
            )
        """)
        # подкидываем демо-вакансию только если таблица совсем пустая
        # которую создали ранее пайтон разработчик
        cur = conn.execute("SELECT COUNT(*) AS n FROM vacancies")
        if cur.fetchone()["n"] == 0:
            conn.execute(
                "INSERT INTO vacancies (title, department, requirements, created_at) VALUES (?,?,?,?)",
                ("Middle Python Developer", "Разработка",
                 "Python, Django, PostgreSQL, Docker, Git", datetime.now().isoformat())
            )


def list_vacancies():
    with _lock, _connect() as conn:
        rows = conn.execute("SELECT * FROM vacancies ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def get_vacancy(vacancy_id):
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,)).fetchone()
        return dict(row) if row else None


def create_vacancy(title, department, requirements):
    with _lock, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO vacancies (title, department, requirements, created_at) VALUES (?,?,?,?)",
            (title, department or "", requirements, datetime.now().isoformat())
        )
        vid = cur.lastrowid
        # возвращаем уже созданную запись, чтобы фронт сразу отрисовал её с id
        row = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vid,)).fetchone()
        return dict(row)


def update_vacancy(vacancy_id, title, department, requirements):
    with _lock, _connect() as conn:
        conn.execute(
            "UPDATE vacancies SET title = ?, department = ?, requirements = ? WHERE id = ?",
            (title, department or "", requirements, vacancy_id)
        )
        row = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,)).fetchone()
        return dict(row) if row else None


def delete_vacancy(vacancy_id):
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))
        # rowcount > 0 значит вакансия реально была и удалилась
        return cur.rowcount > 0


def save_analysis(analysis_id, filename, vacancy_id, vacancy_title,
                  candidate, profile, matching):
    with _lock, _connect() as conn:
        conn.execute(
            """INSERT INTO analyses
               (analysis_id, filename, vacancy_id, vacancy_title, candidate_name,
                total_score, candidate, profile, matching, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (analysis_id, filename, vacancy_id, vacancy_title,
             (candidate or {}).get("name"),
             (matching or {}).get("total_score"),
             json.dumps(candidate, ensure_ascii=False),
             json.dumps(profile, ensure_ascii=False),
             json.dumps(matching, ensure_ascii=False),
             datetime.now().isoformat())
        )


def list_analyses(limit=100, vacancy_id=None):
    # для списка истории тяжёлый JSON не нужен, тянем только то, что видно в таблице
    # vacancy_id передаём, когда хотим историю по конкретной вакансии
    with _lock, _connect() as conn:
        if vacancy_id is not None:
            rows = conn.execute(
                """SELECT analysis_id, filename, vacancy_id, vacancy_title,
                          candidate_name, total_score, created_at
                   FROM analyses WHERE vacancy_id = ?
                   ORDER BY id DESC LIMIT ?""", (vacancy_id, limit)).fetchall()
        else:
            rows = conn.execute(
                """SELECT analysis_id, filename, vacancy_id, vacancy_title,
                          candidate_name, total_score, created_at
                   FROM analyses ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_analysis(analysis_id):
    # "Подробнее" отдает полную запись с разобранным JSON
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE analysis_id = ?", (analysis_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        for f in ("candidate", "profile", "matching"):
            try:
                d[f] = json.loads(d[f]) if d[f] else None
            except (ValueError, TypeError):
                d[f] = None
        return d
