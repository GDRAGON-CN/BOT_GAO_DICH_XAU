import React from 'react';

export default function Header({ currentState, getStatusColor, tradingEnv = 'DEMO' }) {
  const isDemo = tradingEnv.toUpperCase() === 'DEMO';

  return (
    <div className="logo-area">
      <span className="logo-badge">XAUUSD</span>
      <span
        style={{
          backgroundColor: isDemo ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.2)',
          color: isDemo ? 'var(--color-blue)' : 'var(--color-red)',
          border: `1px solid ${isDemo ? 'var(--color-blue)' : 'var(--color-red)'}`,
          padding: '4px 10px',
          borderRadius: '6px',
          fontSize: '12px',
          fontWeight: '700',
          letterSpacing: '0.5px',
        }}
      >
        {isDemo ? '🛡️ DEMO MODE' : '⚠️ LIVE REAL MONEY'}
      </span>
      <div>
        <h1 className="brand-title">Gold Trading Terminal</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          TradingView • FastAPI • Vantage MT5 Demo Terminal
        </p>
      </div>
    </div>
  );
}

