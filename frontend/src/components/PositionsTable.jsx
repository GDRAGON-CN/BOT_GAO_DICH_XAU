import React from 'react';
import { Activity } from 'lucide-react';

export default function PositionsTable({ positions = [] }) {
  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <h2 className="section-title">
        <Activity size={18} /> Open Positions
      </h2>
      {positions.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Ticket</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Lots</th>
              <th>Entry</th>
              <th>Current</th>
              <th>SL / TP</th>
              <th>PnL</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.ticket}>
                <td>#{p.ticket}</td>
                <td><strong>{p.symbol}</strong></td>
                <td>
                  <span className={`badge ${p.side === 'LONG' ? 'badge-long' : 'badge-short'}`}>
                    {p.side}
                  </span>
                </td>
                <td>{p.lots}</td>
                <td>{p.entry_price.toFixed(2)}</td>
                <td>{p.current_price.toFixed(2)}</td>
                <td>{p.stop_loss || '-'} / {p.take_profit || '-'}</td>
                <td style={{ color: p.profit >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
                  ${p.profit.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '16px 0' }}>
          No active positions open. Ready for signals.
        </p>
      )}
    </div>
  );
}
