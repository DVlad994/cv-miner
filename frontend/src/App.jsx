import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import DropZone from './components/DropZone';
import ScoreExplanation from './components/ScoreExplanation';
import { api } from './api';
import './App.css';

// Карточка результата по одному кандидату — одна и та же и в анализе, и в истории,
// поэтому вынесена отдельно, чтобы не дублировать разметку
function CandidateResult({ result }) {
  const m = result.matching_result;
  return (
    <div className="results">
      <div className="score-card">
        <div className="score-circle">
          <span className="score-number">{m.total_score}%</span>
          <span className="score-label">соответствие</span>
        </div>
      </div>

      <ScoreExplanation explanation={m.explanation} />

      <div className="result-card">
        <h3>Кандидат</h3>
        {result.candidate.name && <p><strong>Имя:</strong> {result.candidate.name}</p>}
        {result.candidate.email && <p><strong>Email:</strong> {result.candidate.email}</p>}
        {result.candidate.phone && <p><strong>Телефон:</strong> {result.candidate.phone}</p>}
        {result.profile && (
          <p><strong>Профиль:</strong> {result.profile.level}
            {result.profile.domain ? `, ${result.profile.domain}` : ''}</p>
        )}
        {result.candidate.experience_years > 0 && (
          <p><strong>Опыт:</strong> {result.candidate.experience_years} лет</p>
        )}
        {result.candidate.education?.length > 0 && (
          <p><strong>Образование:</strong> {result.candidate.education.join(', ')}</p>
        )}
      </div>

      <div className="result-card">
        <h3>Навыки ({result.candidate.skills.length})</h3>
        <div className="skills-tags">
          {result.candidate.skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
        </div>
      </div>

      <div className="result-card">
        <h3>Анализ требований</h3>
        <div className="gap-columns">
          <div>
            <h4 className="gap-matched-title">Совпало ({m.matched.length})</h4>
            {m.matched.map(s => <div key={s} className="gap-item matched">{s}</div>)}
          </div>
          {m.partial?.length > 0 && (
            <div>
              <h4 className="gap-partial-title">Частично ({m.partial.length})</h4>
              {m.partial.map(p => (
                <div key={p.requirement} className="gap-item partial"
                  title={`Зачтено через «${p.via}» на ${Math.round(p.credit * 100)}%`}>
                  {p.requirement} ≈ {p.via} ({Math.round(p.credit * 100)}%)
                </div>
              ))}
            </div>
          )}
          <div>
            <h4 className="gap-missing-title">Отсутствует ({m.missing.length})</h4>
            {m.missing.map(s => <div key={s} className="gap-item missing">{s}</div>)}
          </div>
        </div>
      </div>

      {result.full_text && (
        <div className="result-card">
          <h3>Извлечённый текст ({result.text_length} символов)</h3>
          <pre className="result-text">{result.full_text}</pre>
        </div>
      )}
    </div>
  );
}

function App() {
  const [vacancies, setVacancies] = useState([]);
  const [selectedVacancy, setSelectedVacancy] = useState(null);
  const [mode, setMode] = useState('analyze'); // analyze | rank | history

  const [uploadedFile, setUploadedFile] = useState(null);
  const [rankFiles, setRankFiles] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [ranking, setRanking] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyDetail, setHistoryDetail] = useState(null);

  const loadVacancies = useCallback(async () => {
    try {
      const data = await api.listVacancies();
      setVacancies(data);
      setSelectedVacancy(prev => prev ? data.find(v => v.id === prev.id) || null : null);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { loadVacancies(); }, [loadVacancies]);

  const resetOutputs = () => { setResult(null); setRanking(null); setHistoryDetail(null); };

  const handleAnalyze = async () => {
    if (!uploadedFile || !selectedVacancy) return;
    setIsBusy(true); resetOutputs();
    try {
      const fd = new FormData();
      fd.append('file', uploadedFile);
      fd.append('vacancy_id', selectedVacancy.id);
      setResult(await api.analyze(fd));
    } catch (e) { alert('Ошибка: ' + e.message); }
    finally { setIsBusy(false); }
  };

  const handleRank = async () => {
    if (!rankFiles.length || !selectedVacancy) return;
    setIsBusy(true); resetOutputs();
    try {
      const fd = new FormData();
      rankFiles.forEach(f => fd.append('files', f));
      fd.append('vacancy_id', selectedVacancy.id);
      setRanking(await api.rank(fd));
    } catch (e) { alert('Ошибка: ' + e.message); }
    finally { setIsBusy(false); }
  };

  const loadHistory = useCallback(async () => {
    try {
      setHistory(await api.listAnalyses(selectedVacancy?.id));
    } catch (e) { console.error(e); }
  }, [selectedVacancy]);

  useEffect(() => { if (mode === 'history') loadHistory(); }, [mode, loadHistory]);

  const openHistoryItem = async (id) => {
    try {
      const rec = await api.getAnalysis(id);
      setHistoryDetail({
        candidate: rec.candidate, profile: rec.profile,
        matching_result: rec.matching, full_text: null,
      });
    } catch (e) { alert(e.message); }
  };

  const switchMode = (m) => { setMode(m); resetOutputs(); };

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
        <Sidebar
          vacancies={vacancies}
          selectedVacancy={selectedVacancy}
          onSelect={setSelectedVacancy}
          onChanged={loadVacancies}
        />

        <div className="workspace">
          {selectedVacancy ? (
            <>
              <div className="vacancy-card">
                {selectedVacancy.department && (
                  <span className="vacancy-badge">{selectedVacancy.department}</span>
                )}
                <h2 className="vacancy-title">{selectedVacancy.title}</h2>
                <p className="vacancy-desc">{selectedVacancy.requirements}</p>
              </div>

              <div className="mode-tabs">
                <button className={mode === 'analyze' ? 'active' : ''}
                  onClick={() => switchMode('analyze')}>Один кандидат</button>
                <button className={mode === 'rank' ? 'active' : ''}
                  onClick={() => switchMode('rank')}>Ранжирование</button>
                <button className={mode === 'history' ? 'active' : ''}
                  onClick={() => switchMode('history')}>История</button>
              </div>

              {/* загрузил одно резюме — получил разбор */}
              {mode === 'analyze' && (
                <>
                  <DropZone
                    onFileUpload={setUploadedFile}
                    uploadedFile={uploadedFile}
                    onRemoveFile={() => { setUploadedFile(null); setResult(null); }}
                    disabled={false}
                  />
                  {uploadedFile && !isBusy && (
                    <button className="analyze-btn" onClick={handleAnalyze}>
                      Найти совпадения
                    </button>
                  )}
                  {result && <CandidateResult result={result} />}
                </>
              )}

              {/* загрузил стопку резюме — получил рейтинг, кого смотреть первым */}
              {mode === 'rank' && (
                <>
                  <div className="rank-upload">
                    <input type="file" multiple
                      accept=".pdf,.docx,.doc,.png,.jpg,.jpeg"
                      onChange={e => setRankFiles(Array.from(e.target.files))} />
                    {rankFiles.length > 0 && (
                      <p className="rank-files-info">Выбрано файлов: {rankFiles.length}</p>
                    )}
                  </div>
                  {rankFiles.length > 0 && !isBusy && (
                    <button className="analyze-btn" onClick={handleRank}>
                      Ранжировать кандидатов
                    </button>
                  )}
                  {ranking && (
                    <div className="result-card">
                      <h3>Рейтинг кандидатов ({ranking.count})</h3>
                      {ranking.skipped?.length > 0 && (
                        <p className="rank-skipped">Пропущено: {ranking.skipped.join(', ')}</p>
                      )}
                      <table className="rank-table">
                        <thead>
                          <tr><th>#</th><th>Кандидат</th><th>Файл</th>
                            <th>Уровень</th><th>Балл</th></tr>
                        </thead>
                        <tbody>
                          {ranking.ranking.map(r => (
                            <tr key={r.rank}>
                              <td className="rank-place">{r.rank}</td>
                              <td>{r.candidate_name || '—'}</td>
                              <td className="rank-file">{r.filename}</td>
                              <td>{r.level}{r.domain ? `, ${r.domain}` : ''}</td>
                              <td>
                                <div className="rank-score-cell">
                                  <span>{r.total_score}%</span>
                                  <div className="rank-score-bar">
                                    <div style={{ width: `${r.total_score}%` }} />
                                  </div>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {/* прошлые анализы — можно вернуться и не гонять резюме заново */}
              {mode === 'history' && (
                <>
                  <div className="result-card">
                    <h3>История анализов {selectedVacancy ? 'по этой вакансии' : ''}</h3>
                    {history.length === 0 && <p className="rank-skipped">Записей пока нет.</p>}
                    {history.length > 0 && (
                      <table className="rank-table">
                        <thead>
                          <tr><th>Дата</th><th>Кандидат</th><th>Файл</th><th>Балл</th><th></th></tr>
                        </thead>
                        <tbody>
                          {history.map(h => (
                            <tr key={h.analysis_id}>
                              <td>{new Date(h.created_at).toLocaleString('ru-RU')}</td>
                              <td>{h.candidate_name || '—'}</td>
                              <td className="rank-file">{h.filename}</td>
                              <td>{h.total_score}%</td>
                              <td>
                                <button className="link-btn"
                                  onClick={() => openHistoryItem(h.analysis_id)}>
                                  Подробнее
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                  {historyDetail && <CandidateResult result={historyDetail} />}
                </>
              )}

              {isBusy && (
                <div className="progress-container">
                  <div className="progress-bar"><div className="progress-fill"></div></div>
                  <p className="progress-text">Обрабатываем резюме...</p>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📄</div>
              <p>Выберите вакансию из списка</p>
              <span>или добавьте новую, затем загрузите резюме</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
