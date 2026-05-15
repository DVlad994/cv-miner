import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import './App.css';

function App() {
  const [selectedVacancy, setSelectedVacancy] = useState(null);

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
            <p>Выбрана вакансия: {selectedVacancy.title}</p>
          ) : (
            <p className="placeholder">Выберите вакансию из списка</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;