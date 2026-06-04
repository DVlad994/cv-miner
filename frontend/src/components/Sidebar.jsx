import React, { useState } from 'react';
import { api } from '../api';
import './Sidebar.css';

const EMPTY = { title: '', department: '', requirements: '' };

function Sidebar({ vacancies, selectedVacancy, onSelect, onChanged }) {
  const [editing, setEditing] = useState(null); // null — закрыто, 'new' — создаём, объект — правим эту вакансию
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');

  const grouped = vacancies.reduce((acc, v) => {
    const dept = v.department || 'Без отдела';
    (acc[dept] = acc[dept] || []).push(v);
    return acc;
  }, {});

  const openNew = () => { setForm(EMPTY); setEditing('new'); setError(''); };
  const openEdit = (v, e) => {
    e.stopPropagation();
    setForm({ title: v.title, department: v.department || '', requirements: v.requirements });
    setEditing(v); setError('');
  };

  const save = async () => {
    if (!form.title.trim() || !form.requirements.trim()) {
      setError('Заполните название и требования'); return;
    }
    try {
      if (editing === 'new') await api.createVacancy(form);
      else await api.updateVacancy(editing.id, form);
      setEditing(null); onChanged();
    } catch (e) { setError(e.message); }
  };

  const remove = async (v, e) => {
    e.stopPropagation();
    if (!window.confirm(`Удалить вакансию «${v.title}»?`)) return;
    try { await api.deleteVacancy(v.id); onChanged(); } catch (er) { alert(er.message); }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Вакансии</h2>
        <span className="badge">{vacancies.length}</span>
      </div>

      <button className="add-vacancy-btn" onClick={openNew}>+ Добавить вакансию</button>

      <nav className="vacancy-list">
        {Object.entries(grouped).map(([dept, vacs]) => (
          <div key={dept}>
            <div className="dept-label">{dept}</div>
            {vacs.map(v => (
              <div
                key={v.id}
                className={`vacancy-item ${selectedVacancy?.id === v.id ? 'active' : ''}`}
                onClick={() => onSelect(v)}
              >
                <div className="vacancy-item-main">
                  <div className="vacancy-title">{v.title}</div>
                  <div className="vacancy-hint">{v.requirements}</div>
                </div>
                <div className="vacancy-actions">
                  <button title="Редактировать" onClick={(e) => openEdit(v, e)}>✎</button>
                  <button title="Удалить" onClick={(e) => remove(v, e)}>🗑</button>
                </div>
              </div>
            ))}
          </div>
        ))}
        {vacancies.length === 0 && (
          <p className="sidebar-empty">Вакансий пока нет. Добавьте первую.</p>
        )}
      </nav>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editing === 'new' ? 'Новая вакансия' : 'Редактирование вакансии'}</h3>
            <label>Название
              <input value={form.title}
                onChange={e => setForm({ ...form, title: e.target.value })}
                placeholder="Например, Middle Python Developer" />
            </label>
            <label>Отдел
              <input value={form.department}
                onChange={e => setForm({ ...form, department: e.target.value })}
                placeholder="Например, Разработка" />
            </label>
            <label>Требования (навыки через запятую)
              <textarea value={form.requirements} rows={4}
                onChange={e => setForm({ ...form, requirements: e.target.value })}
                placeholder="Python, Django, PostgreSQL, Docker, Git" />
            </label>
            {error && <p className="modal-error">{error}</p>}
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setEditing(null)}>Отмена</button>
              <button className="btn-primary" onClick={save}>Сохранить</button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
