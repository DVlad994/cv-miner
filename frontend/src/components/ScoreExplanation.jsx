import React from 'react';
import './ScoreExplanation.css';

// Показываем, из чего сложился балл: полоски вклада по факторам и пояснения словами
// чтобы HR видел не просто "76%", а почему именно столько
function ScoreExplanation({ explanation }) {
  if (!explanation) return null;
  const { summary, breakdown, notes } = explanation;

  return (
    <div className="result-card">
      <h3>Почему такой балл</h3>
      <p className="explain-summary">{summary}</p>

      <div className="explain-factors">
        {breakdown.map(b => (
          <div key={b.factor} className="explain-factor">
            <div className="explain-factor-head">
              <span className="explain-factor-name">{b.label}</span>
              <span className="explain-factor-val">
                +{b.contribution} / {b.max_contribution} б.
              </span>
            </div>
            <div className="explain-bar">
              <div
                className="explain-bar-fill"
                style={{ width: `${b.value * 100}%` }}
                title={`Фактор закрыт на ${Math.round(b.value * 100)}%`}
              />
            </div>
          </div>
        ))}
      </div>

      {notes?.length > 0 && (
        <ul className="explain-notes">
          {notes.map((n, i) => <li key={i}>{n}</li>)}
        </ul>
      )}
    </div>
  );
}

export default ScoreExplanation;
