import React from 'react';
import { Wallet, TrendingUp, Scale, ShieldAlert, DollarSign, AlertTriangle, Percent } from 'lucide-react';

export default function MetricsGrid({ account = {}, openPositionsCount = 0, todayPnl = 0, dailyLoss = 0 }) {
  const balance = account.balance !== undefined ? account.balance : 0.0;
  const equity = account.equity !== undefined ? account.equity : 0.0;
  const freeMargin = account.free_margin !== undefined ? account.free_margin : 0.0;
  const marginLevel = account.margin_level !== undefined ? account.margin_level : 0.0;

  return (
    <section className="metrics-grid">
      <div className="card">
        <div className="card-title">
          <Wallet size={14} style={{ display: 'inline', marginRight: '6px' }} /> Account Balance
        </div>
        <div className="card-value">${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        <div className="card-subtitle">Server: {account.server || 'VantageInternational-Live'}</div>
      </div>

      <div className="card">
        <div className="card-title">
          <TrendingUp size={14} style={{ display: 'inline', marginRight: '6px' }} /> Account Equity
        </div>
        <div className="card-value" style={{ color: equity >= balance ? 'var(--color-green)' : 'var(--color-red)' }}>
          ${equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="card-subtitle">Free Margin: ${freeMargin.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      </div>

      <div className="card">
        <div className="card-title">
          <Percent size={14} style={{ display: 'inline', marginRight: '6px' }} /> Margin Level
        </div>
        <div className="card-value" style={{ color: marginLevel > 200 || marginLevel === 0 ? 'var(--color-green)' : 'var(--accent-gold)' }}>
          {marginLevel > 0 ? `${marginLevel.toFixed(1)}%` : 'N/A (No Margin)'}
        </div>
        <div className="card-subtitle">Stop-out threshold: 50.0%</div>
      </div>

      <div className="card">
        <div className="card-title">
          <DollarSign size={14} style={{ display: 'inline', marginRight: '6px' }} /> Today's P/L
        </div>
        <div className="card-value" style={{ color: todayPnl >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
          {todayPnl >= 0 ? `+$${todayPnl.toFixed(2)}` : `-$${Math.abs(todayPnl).toFixed(2)}`}
        </div>
        <div className="card-subtitle">Realized Closed Positions</div>
      </div>

      <div className="card">
        <div className="card-title">
          <AlertTriangle size={14} style={{ display: 'inline', marginRight: '6px' }} /> Daily Loss
        </div>
        <div className="card-value" style={{ color: dailyLoss > 0 ? 'var(--color-red)' : 'var(--text-main)' }}>
          ${dailyLoss.toFixed(2)}
        </div>
        <div className="card-subtitle">Daily Loss Cap: $300.00 (3.0%)</div>
      </div>

      <div className="card">
        <div className="card-title">
          <Scale size={14} style={{ display: 'inline', marginRight: '6px' }} /> Active Positions
        </div>
        <div className="card-value">{openPositionsCount}</div>
        <div className="card-subtitle">Max Allowed: 2 Positions</div>
      </div>
    </section>
  );
}

