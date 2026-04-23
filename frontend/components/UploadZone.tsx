'use client';

import { useState } from 'react';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFileSelect, disabled }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div 
      className={`glass-card ${isDragging ? 'dragging' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      style={{
        border: isDragging ? '2px dashed var(--primary)' : '1px solid var(--border)',
        textAlign: 'center',
        padding: '3rem 2rem',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s ease',
        background: isDragging ? 'rgba(59, 130, 246, 0.05)' : 'var(--surface)'
      }}
      onClick={() => !disabled && document.getElementById('file-input')?.click()}
    >
      <input 
        id="file-input"
        type="file" 
        hidden 
        onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
        accept=".pdf,.docx,.txt,.jpg,.png"
      />
      
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
      <h2 style={{ marginBottom: '0.5rem' }}>Upload Study Material</h2>
      <p style={{ color: 'var(--secondary)', marginBottom: '1.5rem' }}>
        Drop your PDF, Docx, or Images here to generate a quiz
      </p>
      
      <div className="btn-premium" style={{ display: 'inline-flex' }}>
        Select File
      </div>
    </div>
  );
}
