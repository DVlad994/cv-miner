import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import DropZone from './components/DropZone';
import './App.css';

function App() {
  const [selectedVacancy, setSelectedVacancy] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!uploadedFile || !selectedVacancy) return;

    setIsAnalyzing(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('vacancy_text', selectedVacancy.requirements);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert('Ошибка: ' + (errorData.error || 'Неизвестная ошибка'));
        setIsAnalyzing(false);
        return;
      }

      const data = await response.json();
      setResult(data);
      console.log('Результат:', data);
    } catch (error) {
      console.error('Ошибка:', error);
      alert('Ошибка соединения с сервером.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo-icon">CV</div>
          <span className="logo-text">CV-Miner</span>
        </div>
        <div className="header-right">
          <span className="status-dot"></span>
          <span className="status-text">Система работает</span>
        </div>
      </header>

      <div className="main-layout">
        <Sidebar selectedVacancy={selectedVacancy} onSelect={setSelectedVacancy} />

        <div className="workspace">
          {selectedVacancy ? (
            <>
              <div className="vacancy-card">
                <span className="vacancy-badge">{selectedVacancy.department}</span>
                <h2 className="vacancy-title">{selectedVacancy.title}</h2>
                <p className="vacancy-desc">{selectedVacancy.requirements}</p>
              </div>

              <DropZone
                onFileUpload={setUploadedFile}
                uploadedFile={uploadedFile}
                onRemoveFile={() => {
                  setUploadedFile(null);
                  setResult(null);
                }}
                disabled={!selectedVacancy}
              />

              {uploadedFile && (
                <button
                  className="analyze-btn"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? 'Анализируем...' : 'Найти совпадения'}
                </button>
              )}

              {result && (
                <>
                  {/* Общий рейтинг на основе навыков и опыта */}
                  <div className="score-card">
                    <div className="score-circle">
                      <span className="score-number">{result.matching_result.total_score}%</span>
                      <span className="score-label">совпадение</span>
                    </div>
                  </div>

                  {/* Информация о соискателе */}
                  <div className="result-card">
                    <h3>Кандидат</h3>
                    {result.candidate.name && <p><strong>Имя:</strong> {result.candidate.name}</p>}
                    {result.candidate.email && <p><strong>Email:</strong> {result.candidate.email}</p>}
                    {result.candidate.phone && <p><strong>Телефон:</strong> {result.candidate.phone}</p>}
                    {result.candidate.last_position && <p><strong>Последняя должность:</strong> {result.candidate.last_position}</p>}
                    {result.candidate.experience_years && <p><strong>Опыт:</strong> {result.candidate.experience_years} лет</p>}
                    <div className="skills-tags">
                      {result.candidate.skills.map(skill => (
                        <span key={skill} className="skill-tag">{skill}</span>
                      ))}
                    </div>
                  </div>

                  {/* Gap-анализ */}
                  <div className="result-card">
                    <h3>Gap-анализ</h3>
                    <div className="gap-columns">
                      <div>
                        <h4>Совпало ({result.matching_result.matched.length})</h4>
                        {result.matching_result.matched.map(s => (
                          <div key={s} className="gap-item matched">{s}</div>
                        ))}
                      </div>
                      <div>
                        <h4>Отсутствует ({result.matching_result.missing.length})</h4>
                        {result.matching_result.missing.map(s => (
                          <div key={s} className="gap-item missing">{s}</div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Полный текст резюме */}
                  <div className="result-card">
                    <h3>Извлечённый текст ({result.text_length} символов)</h3>
                    <pre className="result-text">{result.full_text}</pre>
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📄</div>
              <p>Выберите вакансию из списка</p>
              <span>и загрузите резюме для анализа</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;