// Все запросы к бэку в одном месте, чтобы по компонентам не плодить fetch и url
const BASE = 'http://localhost:8000/api';

// единая обработка ответа: на ошибке достаём текст из {error} и кидаем исключение,
// чтобы в компонентах ловить через try/catch и показывать алерт
async function handle(res) {
  if (!res.ok) {
    let msg = 'Ошибка запроса';
    try { msg = (await res.json()).error || msg; } catch (e) { /* тело не json — оставляем дефолт */ }
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  // вакансии (CRUD из сайдбара)
  listVacancies: () => fetch(`${BASE}/vacancies`).then(handle),
  createVacancy: (v) => fetch(`${BASE}/vacancies`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(v),
  }).then(handle),
  updateVacancy: (id, v) => fetch(`${BASE}/vacancies/${id}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(v),
  }).then(handle),
  deleteVacancy: (id) => fetch(`${BASE}/vacancies/${id}`, { method: 'DELETE' }).then(handle),

  // анализ одного резюме и ранжирование пачки (оба шлют FormData с файлами)
  analyze: (formData) => fetch(`${BASE}/analyze`, { method: 'POST', body: formData }).then(handle),
  rank: (formData) => fetch(`${BASE}/rank`, { method: 'POST', body: formData }).then(handle),

  // история: список и полная карточка по клику
  listAnalyses: (vacancyId) => fetch(
    `${BASE}/analyses${vacancyId ? `?vacancy_id=${vacancyId}` : ''}`).then(handle),
  getAnalysis: (id) => fetch(`${BASE}/analyses/${id}`).then(handle),
};
