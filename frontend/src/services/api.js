const API_BASE = 'http://127.0.0.1:8000/api/v1';
const API_KEY = 'dash_local_secret_123456';

export async function fetchStatus() {
  const res = await fetch(`${API_BASE}/control/status`);
  if (!res.ok) throw new Error('Status query failed');
  return res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/dashboard/metrics`);
  if (!res.ok) throw new Error('Metrics query failed');
  return res.json();
}

export async function fetchHistory(resource, limit = 50) {
  const res = await fetch(`${API_BASE}/dashboard/history/${resource}?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch history for ${resource}`);
  return res.json();
}

export async function sendControlCommand(command) {
  const res = await fetch(`${API_BASE}/control/${command}?operator=DASHBOARD_UI`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY },
  });
  if (!res.ok) throw new Error(`Command ${command} failed`);
  return res.json();
}

