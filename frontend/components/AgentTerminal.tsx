'use client';

import { useEffect, useRef, useState } from 'react';

interface LogEntry {
  message: string;
  type: 'info' | 'agent' | 'success' | 'error';
  timestamp: string;
}

export default function AgentTerminal({ isRunning }: { isRunning: boolean }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  // Simulate or connect to actual SSE if implementation supports it
  useEffect(() => {
    if (!isRunning) return;

    // In a real implementation, we'd use new EventSource('/api/logs')
    // For now, let's keep the terminal ready for data injection
  }, [isRunning]);

  const addLog = (message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [...prev, {
      message,
      type,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  return (
    <div className="glass-card" style={{ padding: '1rem', height: '300px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        <h3 style={{ fontSize: '0.9rem', color: 'var(--secondary)', textTransform: 'uppercase' }}>Agent Terminal</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isRunning ? 'var(--accent)' : 'var(--secondary)' }}></div>
        </div>
      </div>
      <div 
        ref={scrollRef}
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          fontFamily: 'monospace', 
          fontSize: '0.85rem',
          lineHeight: '1.4'
        }}
      >
        {logs.length === 0 && (
          <div style={{ color: 'var(--secondary)', opacity: 0.5 }}>Waiting for agent initialization...</div>
        )}
        {logs.map((log, i) => (
          <div key={i} style={{ marginBottom: '0.25rem', display: 'flex', gap: '0.5rem' }}>
            <span style={{ color: 'var(--secondary)', minWidth: '70px' }}>[{log.timestamp}]</span>
            <span style={{ 
              color: log.type === 'agent' ? '#a78bfa' : 
                     log.type === 'success' ? 'var(--accent)' : 
                     log.type === 'error' ? 'var(--error)' : 'inherit'
            }}>
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
