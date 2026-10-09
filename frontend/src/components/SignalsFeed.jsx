import React from 'react';
import { RefreshCw } from 'lucide-react';

export default function SignalsFeed({ signals = [] }) {
  return (
    <div className="card">
      <h2 className="section-title">
        <RefreshCw size={18} /> Recent TradingView Signals
      </h2>
      <div className="log-list">
        {signals.length > 0 ? (
          signals.map((s) => (
            <div className="log-item" key={s.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong>{s.action} {s.symbol}</strong>
                <span className={`badge ${s.status === 'EXECUTED' ? 'badge-long' : 'badge-short'}`}>
                  {s.status}
                </span>
              </div>
              {s.rejection_reason && (
                <p style={{ color: 'var(--color-red)', fontSize: '11px', marginTop: '4px' }}>
                  {s.rejection_reason}
                </p>
              )}
              <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>{s.created_at}</span>
            </div>
          ))
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Awaiting webhooks...</p>
        )}
      </div>
    </div>
  );
}
