import React, { useState, useEffect } from 'react';
import { fetchHistory } from '../services/api';
import { Clock, ShieldAlert, FileText, CheckCircle2, History, AlertCircle, RefreshCw } from 'lucide-react';

const TABS = [
  { key: 'signals', label: 'Signals', icon: RefreshCw },
  { key: 'orders', label: 'Orders', icon: FileText },
  { key: 'positions', label: 'Positions', icon: CheckCircle2 },
  { key: 'trades', label: 'Trades', icon: History },
  { key: 'risk-events', label: 'Risk Events', icon: ShieldAlert },
  { key: 'bot-events', label: 'Bot Events', icon: AlertCircle },
];

export default function HistoryViewer() {
  const [activeTab, setActiveTab] = useState('signals');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadTabHistory = async (tabKey) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchHistory(tabKey, 50);
      setData(result || []);
    } catch (err) {
      setError(err.message || 'Failed to load historical data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTabHistory(activeTab);
  }, [activeTab]);

  return (
    <div className="card" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={18} style={{ color: 'var(--accent-gold)' }} />
          <h2 className="section-title" style={{ margin: 0 }}>System History & Auditing</h2>
        </div>
        
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className="btn"
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  backgroundColor: isActive ? 'var(--accent-gold)' : 'var(--bg-dark)',
                  color: isActive ? '#000' : 'var(--text-muted)',
                  border: `1px solid ${isActive ? 'var(--accent-gold)' : 'var(--border-color)'}`,
                  fontWeight: isActive ? '700' : '500'
                }}
              >
                <Icon size={13} /> {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '20px 0' }}>Loading historical data...</p>
      ) : error ? (
        <p style={{ color: 'var(--color-red)', fontSize: '13px', padding: '20px 0' }}>{error}</p>
      ) : data.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '20px 0' }}>No records found for {activeTab}.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          {activeTab === 'signals' && (
            <table>
              <thead>
                <tr>
                  <th>UUID</th>
                  <th>Symbol</th>
                  <th>Action</th>
                  <th>Timeframe</th>
                  <th>Target</th>
                  <th>SL / TP</th>
                  <th>Status</th>
                  <th>Rejection Details</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {data.map((s) => (
                  <tr key={s.id || s.signal_uuid}>
                    <td style={{ fontSize: '11px' }}>{(s.signal_uuid || '').slice(0, 8)}...</td>
                    <td><strong>{s.symbol}</strong></td>
                    <td>
                      <span className={`badge ${s.action === 'BUY' ? 'badge-long' : 'badge-short'}`}>
                        {s.action}
                      </span>
                    </td>
                    <td>{s.timeframe}</td>
                    <td>{s.target_price ? `$${s.target_price.toFixed(2)}` : '-'}</td>
                    <td>{s.stop_loss ? `$${s.stop_loss.toFixed(2)}` : '-'} / {s.take_profit ? `$${s.take_profit.toFixed(2)}` : '-'}</td>
                    <td><span className={`badge ${s.status === 'EXECUTED' ? 'badge-long' : 'badge-short'}`}>{s.status}</span></td>
                    <td style={{ color: s.rejection_reason ? 'var(--color-red)' : 'var(--text-muted)', fontSize: '11px' }}>
                      {s.rejection_reason || 'None'}
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{s.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'orders' && (
            <table>
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Symbol</th>
                  <th>Type</th>
                  <th>Requested Lots</th>
                  <th>Filled Lots</th>
                  <th>Requested Price</th>
                  <th>Execution Price</th>
                  <th>Status</th>
                  <th>Submitted At</th>
                </tr>
              </thead>
              <tbody>
                {data.map((o) => (
                  <tr key={o.id}>
                    <td>#{o.ticket}</td>
                    <td><strong>{o.symbol}</strong></td>
                    <td>{o.order_type}</td>
                    <td>{o.requested_lots}</td>
                    <td>{o.filled_lots}</td>
                    <td>${o.requested_price.toFixed(2)}</td>
                    <td>{o.execution_price ? `$${o.execution_price.toFixed(2)}` : '-'}</td>
                    <td><span className="badge badge-exec">{o.status}</span></td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{o.submitted_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'positions' && (
            <table>
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Lots</th>
                  <th>Entry Price</th>
                  <th>SL / TP</th>
                  <th>Status</th>
                  <th>Opened At</th>
                  <th>Closed At</th>
                </tr>
              </thead>
              <tbody>
                {data.map((p) => (
                  <tr key={p.id}>
                    <td>#{p.ticket}</td>
                    <td><strong>{p.symbol}</strong></td>
                    <td>
                      <span className={`badge ${p.side === 'LONG' ? 'badge-long' : 'badge-short'}`}>
                        {p.side}
                      </span>
                    </td>
                    <td>{p.current_lots}</td>
                    <td>${p.entry_price.toFixed(2)}</td>
                    <td>{p.stop_loss ? `$${p.stop_loss.toFixed(2)}` : '-'} / {p.take_profit ? `$${p.take_profit.toFixed(2)}` : '-'}</td>
                    <td><span className="badge badge-exec">{p.status}</span></td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.opened_at}</td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.closed_at || 'Active'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'trades' && (
            <table>
              <thead>
                <tr>
                  <th>Trade ID</th>
                  <th>Position ID</th>
                  <th>Close Price</th>
                  <th>Net Profit ($)</th>
                  <th>Commission</th>
                  <th>Swap</th>
                  <th>Pips</th>
                  <th>Exit Reason</th>
                  <th>Closed At</th>
                </tr>
              </thead>
              <tbody>
                {data.map((t) => (
                  <tr key={t.id}>
                    <td>#{t.id}</td>
                    <td>#{t.position_id}</td>
                    <td>${t.close_price.toFixed(2)}</td>
                    <td style={{ color: t.net_profit >= 0 ? 'var(--color-green)' : 'var(--color-red)', fontWeight: 'bold' }}>
                      ${t.net_profit.toFixed(2)}
                    </td>
                    <td>${t.commission.toFixed(2)}</td>
                    <td>${t.swap.toFixed(2)}</td>
                    <td>{t.pips.toFixed(1)}</td>
                    <td><span className="badge badge-exec">{t.exit_reason}</span></td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t.closed_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'risk-events' && (
            <table>
              <thead>
                <tr>
                  <th>Event Type</th>
                  <th>Rule Name</th>
                  <th>Threshold</th>
                  <th>Actual Value</th>
                  <th>Action Taken</th>
                  <th>Details</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <tr key={r.id}>
                    <td><span className="badge badge-short">{r.event_type}</span></td>
                    <td><strong>{r.rule_name}</strong></td>
                    <td>{r.threshold_value || '-'}</td>
                    <td>{r.actual_value || '-'}</td>
                    <td><span className="badge badge-exec">{r.system_action_taken}</span></td>
                    <td style={{ fontSize: '11px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.details || '-'}
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'bot-events' && (
            <table>
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Transition</th>
                  <th>Triggered By</th>
                  <th>Message</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {data.map((b) => (
                  <tr key={b.id}>
                    <td><span className="badge badge-exec">{b.event_category}</span></td>
                    <td>{b.previous_state || 'NONE'} → <strong>{b.new_state || 'NONE'}</strong></td>
                    <td>{b.triggered_by}</td>
                    <td style={{ fontSize: '12px' }}>{b.message}</td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{b.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
