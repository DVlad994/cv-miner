import React from 'react';
import './Sidebar.css';

const VACANCIES = [
  { id: 1, title: 'Middle Python Developer', department: 'Разработка', requirements: 'Python, Django, PostgreSQL, Docker, Git' }
];

function Sidebar({ selectedVacancy, onSelect }) {
  const grouped = VACANCIES.reduce((acc, v) => {
    if (!acc[v.department]) acc[v.department] = [];
    acc[v.department].push(v);
    return acc;
  }, {});

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Вакансии</h2>
        <span className="badge">{VACANCIES.length}</span>
      </div>
      <nav>
        {Object.entries(grouped).map(([dept, vacs]) => (
          <div key={dept}>
            <div className="dept-label">{dept}</div>
            {vacs.map(v => (
              <button
                key={v.id}
                className={`vacancy-item ${selectedVacancy?.id === v.id ? 'active' : ''}`}
                onClick={() => onSelect(v)}
              >
                <div>
                  <div className="vacancy-title">{v.title}</div>
                  <div className="vacancy-hint">{v.requirements}</div>
                </div>
              </button>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;