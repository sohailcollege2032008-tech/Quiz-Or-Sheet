'use client';

import { useState, useEffect, useRef } from 'react';
import UploadZone from '@/components/UploadZone';
import AgentTerminal from '@/components/AgentTerminal';
import { generateStandaloneQuiz } from '@/lib/quizGenerator';

interface LogEntry {
  message: string;
  type: 'info' | 'agent' | 'success' | 'error';
  timestamp: string;
}

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [mounted, setMounted] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [...prev, {
      message,
      type,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const handleFileSelect = async (file: File) => {
    setCurrentFile(file);
    setIsProcessing(true);
    setLogs([]);
    addLog(`System initialized. Target: ${file.name}`, 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const apiUrl = `${baseUrl.replace(/\/$/, '')}/process`;
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Backend connection failed');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) throw new Error('No stream readable');

      let currentEvent = 'log';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // SSE chunks are separated by double newlines
        const chunks = buffer.split(/\n\n|\r\n\r\n/);
        buffer = chunks.pop() || '';

        for (const chunk of chunks) {
          const lines = chunk.split(/\n|\r\n/);
          for (const line of lines) {
            if (line.startsWith('event:')) {
              currentEvent = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              const data = line.replace('data:', '').trim();
              
              if (currentEvent === 'log') {
                addLog(data, 'agent');
              } else if (currentEvent === 'result') {
                try {
                  const questions = JSON.parse(data);
                  addLog(`Generated ${questions.length} questions successfully!`, 'success');
                  const html = generateStandaloneQuiz(questions, file.name);
                  downloadFile(html, `${file.name.split('.')[0]}_Quiz.html`);
                } catch (e) {
                  console.error('Failed to parse result data:', data);
                }
              } else if (currentEvent === 'error') {
                addLog(data, 'error');
              } else if (currentEvent === 'done') {
                addLog(data, 'success');
                setIsProcessing(false);
              }
            }
          }
        }
      }
    } catch (error: any) {
      addLog(`Error: ${error.message}`, 'error');
      setIsProcessing(false);
    }
  };

  const downloadFile = (content: string, fileName: string) => {
    const blob = new Blob([content], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      <header style={{ textAlign: 'center', marginBottom: '4rem' }} className="animate-fade-in">
        <h1 style={{ fontSize: '3.5rem', marginBottom: '1rem', background: 'linear-gradient(to right, #3b82f6, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Quiz Or Sheet v2
        </h1>
        <p style={{ color: 'var(--secondary)', fontSize: '1.2rem' }}>
          Agentic AI Workflow for Medical Education
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', alignItems: 'start' }}>
        <section className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <UploadZone onFileSelect={handleFileSelect} disabled={isProcessing} />
          
          {currentFile && (
            <div className="glass-card" style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ fontSize: '1.5rem' }}>📄</div>
              <div>
                <div style={{ fontWeight: '600' }}>{currentFile.name}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--secondary)' }}>
                  {(currentFile.size / 1024).toFixed(1)} KB • {currentFile.type.split('/')[1].toUpperCase()}
                </div>
              </div>
            </div>
          )}
        </section>

        <section className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="glass-card" style={{ padding: '1rem', height: '100%', minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '0.9rem', color: 'var(--secondary)', textTransform: 'uppercase' }}>Agent Terminal</h3>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <div style={{ 
                  width: '8px', 
                  height: '8px', 
                  borderRadius: '50%', 
                  background: isProcessing ? '#10b981' : '#64748b',
                  boxShadow: isProcessing ? '0 0 8px #10b981' : 'none'
                }}></div>
                <span style={{ fontSize: '0.75rem', color: 'var(--secondary)' }}>
                  {isProcessing ? 'AGENT ACTIVE' : 'IDLE'}
                </span>
              </div>
            </div>
            
            <div 
              ref={scrollRef}
              style={{ 
                flex: 1, 
                overflowY: 'auto', 
                fontFamily: 'monospace', 
                fontSize: '0.85rem',
                lineHeight: '1.6',
                paddingRight: '0.5rem'
              }}
            >
              {!mounted ? (
                <div style={{ color: 'var(--secondary)', opacity: 0.5, textAlign: 'center', marginTop: '2rem' }}>
                  Initializing...
                </div>
              ) : logs.length === 0 ? (
                <div style={{ color: 'var(--secondary)', opacity: 0.5, textAlign: 'center', marginTop: '2rem' }}>
                  Ready to process documents.
                </div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.75rem' }}>
                    <span style={{ color: 'var(--secondary)', opacity: 0.6, fontSize: '0.75rem', marginTop: '2px' }}>
                      {log.timestamp}
                    </span>
                    <span style={{ 
                      color: log.type === 'agent' ? '#a78bfa' : 
                             log.type === 'success' ? '#10b981' : 
                             log.type === 'error' ? '#ef4444' : 'inherit',
                      wordBreak: 'break-word'
                    }}>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>

      <footer style={{ marginTop: '4rem', textAlign: 'center', color: 'var(--secondary)', fontSize: '0.9rem' }}>
        Built for Al-Azhar University Students • Agentic V2.0
      </footer>
    </main>
  );
}
