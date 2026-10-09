import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StateControls from './components/StateControls';
import MetricsGrid from './components/MetricsGrid';
import PositionsTable from './components/PositionsTable';
import OrdersHistory from './components/OrdersHistory';
import SignalsFeed from './components/SignalsFeed';
import HistoryViewer from './components/HistoryViewer';
import { fetchStatus, fetchMetrics, sendControlCommand } from './services/api';

export default function App() {
  const [botStatus, setBotStatus] = useState({ current_state: 'UNKNOWN', is_running: false });
  const [metrics, setMetrics] = useState({
    account: {},
    open_positions: [],
    recent_signals: [],
    recent_orders: [],
    today_pnl: 0,
    daily_loss: 0,
    recent_trades: [],
    recent_risk_events: [],
    recent_bot_events: [],
  });
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const [status, data] = await Promise.all([fetchStatus(), fetchMetrics()]);
      setBotStatus(status);
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load telemetry data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleCommand = async (command) => {
    setLoading(true);
    try {
      await sendControlCommand(command);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    if (botStatus.current_state === 'RUNNING') return 'dot-green';
    if (botStatus.current_state === 'PAUSED') return 'dot-yellow';
    return 'dot-red';
  };

  return (
    <div className="dashboard-container">
      <header className="header-bar">
        <Header
          currentState={botStatus.current_state}
          getStatusColor={getStatusColor}
          tradingEnv={metrics.trading_env || 'DEMO'}
        />
        <StateControls

          currentState={botStatus.current_state}
          loading={loading}
          onCommand={handleCommand}
          getStatusColor={getStatusColor}
        />
      </header>

      <MetricsGrid
        account={metrics.account}
        openPositionsCount={metrics.open_positions ? metrics.open_positions.length : 0}
        todayPnl={metrics.today_pnl || 0}
        dailyLoss={metrics.daily_loss || 0}
      />

      <div className="content-grid">
        <div>
          <PositionsTable positions={metrics.open_positions || []} />
          <OrdersHistory orders={metrics.recent_orders || []} />
        </div>
        <div>
          <SignalsFeed signals={metrics.recent_signals || []} />
        </div>
      </div>

      <HistoryViewer />
    </div>
  );
}

