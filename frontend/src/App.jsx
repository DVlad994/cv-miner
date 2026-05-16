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
      {/* Шапка */}
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

      {/* Основная область */}
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
                <div className="result-card">
                  <h3>Текст извлечён</h3>
                  <div className="result-info">
                    <span>Файл: {result.filename}</span>
                    <span>Символов: {result.text_length}</span>
                  </div>
                  <pre className="result-text">{result.full_text}</pre>
                </div>
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