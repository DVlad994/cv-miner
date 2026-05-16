import React, { useState, useRef } from 'react';
import './DropZone.css';

function DropZone({ onFileUpload, uploadedFile, onRemoveFile, disabled }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) onFileUpload(file);
  };

  const handleClick = () => {
    if (!disabled) fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileUpload(file);
    }
    // Сбрасываем value, чтобы можно было выбрать тот же файл повторно
    e.target.value = '';
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' Б';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' КБ';
    return (bytes / (1024 * 1024)).toFixed(1) + ' МБ';
  };

  return (
    <div className="dropzone-wrapper">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.png,.jpg"
        onChange={handleFileChange}
        className="file-input"
      />

      {!uploadedFile ? (
        <div
          className={`dropzone ${isDragOver ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <div className="dropzone-icon">+</div>
          <div className="dropzone-text">
            <span className="dropzone-primary">Перетащите резюме сюда</span>
            <span className="dropzone-secondary">или нажмите для выбора</span>
          </div>
          <div className="dropzone-formats">PDF, DOCX, PNG, JPG до 15 МБ</div>
        </div>
      ) : (
        <div className="file-preview">
          <div className="file-info">
            <span className="file-name">{uploadedFile.name}</span>
            <span className="file-size">{formatSize(uploadedFile.size)}</span>
          </div>
          <div className="file-actions">
            <button
              className="file-replace"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
            >
              Загрузить другое резюме
            </button>
            <button
              className="file-remove"
              onClick={(e) => {
                e.stopPropagation();
                onRemoveFile();
              }}
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DropZone;