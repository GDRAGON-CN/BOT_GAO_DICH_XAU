import React from 'react';
import { TrendingUp } from 'lucide-react';

export default function OrdersHistory({ orders = [] }) {
  return (
    <div className="card">
      <h2 className="section-title">
        <TrendingUp size={18} /> Executed Orders History
      </h2>
      {orders.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Ticket</th>
              <th>Symbol</th>
              <th>Type</th>
              <th>Lots</th>
              <th>Fill Price</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>#{o.ticket}</td>
                <td>{o.symbol}</td>
                <td>{o.type}</td>
                <td>{o.lots}</td>
                <td>${o.price.toFixed(2)}</td>
                <td><span className="badge badge-exec">{o.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '16px 0' }}>
          No orders filled yet.
        </p>
      )}
    </div>
  );
}
