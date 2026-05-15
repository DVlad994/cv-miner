import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import DropZone from './components/DropZone';
import './App.css';

function App() {
  const [selectedVacancy, setSelectedVacancy] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  return (
    <div className="app">
      <header className="header">
        <span className="logo">CV-Miner</span>
        <span className="status">● Система работает</span>
      </header>
      <main className="main">
        <Sidebar selectedVacancy={selectedVacancy} onSelect={setSelectedVacancy} />
        <section className="content">
          {selectedVacancy ? (
            <div>
              <div className="vacancy-preview">
                <span className="dept-label">{selectedVacancy.department}</span>
                <h3>{selectedVacancy.title}</h3>
                <p className="vacancy-req">{selectedVacancy.requirements}</p>
              </div>
              <DropZone
                onFileUpload={setUploadedFile}
                uploadedFile={uploadedFile}
                onRemoveFile={() => setUploadedFile(null)}
                disabled={!selectedVacancy}
              />
              {uploadedFile && (
                <button className="analyze-btn" onClick={() => alert('Анализ...')}>
                  Найти совпадения
                </button>
              )}
            </div>
          ) : (
            <p className="placeholder">Выберите вакансию из списка слева</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;