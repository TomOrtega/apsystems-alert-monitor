const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error de API');
  }
  return res.json();
}

export const api = {
  health: () => request('/api/health'),
  dashboard: () => request('/api/dashboard'),
  sistemas: (cuenta, estado) => {
    const params = new URLSearchParams();
    if (cuenta) params.set('cuenta', cuenta);
    if (estado) params.set('estado', estado);
    const q = params.toString();
    return request(`/api/sistemas${q ? '?' + q : ''}`);
  },
  sistema: (sid) => request(`/api/sistemas/${sid}`),
  renameSistema: (sid, nombre) => request(`/api/sistemas/${sid}/nombre`, { method: 'PUT', body: JSON.stringify({ nombre }) }),
  deleteSistema: (sid) => request(`/api/sistemas/${sid}`, { method: 'DELETE' }),
  alertas: (params = {}) => {
    const q = new URLSearchParams();
    if (params.severidad) q.set('severidad', params.severidad);
    if (params.sid) q.set('sid', params.sid);
    if (params.cuenta) q.set('cuenta', params.cuenta);
    if (params.limit) q.set('limit', params.limit);
    if (params.offset) q.set('offset', params.offset);
    const qs = q.toString();
    return request(`/api/alertas${qs ? '?' + qs : ''}`);
  },
  reportes: (dias = 30) => request(`/api/reportes?dias=${dias}`),
  config: () => request('/api/config'),
  configSection: (section) => request(`/api/config/${section}`),
  updateConfig: (section, key, value) => request(`/api/config/${section}/${key}`, { method: 'PUT', body: JSON.stringify({ value }) }),
  accounts: () => request('/api/accounts'),
  addAccount: (data) => request('/api/accounts', { method: 'POST', body: JSON.stringify(data) }),
  deleteAccount: (index) => request(`/api/accounts/${index}`, { method: 'DELETE' }),
  testAccount: (index) => request(`/api/accounts/${index}/test`, { method: 'POST' }),
  updateSmtp: (data) => request('/api/config/smtp', { method: 'PUT', body: JSON.stringify(data) }),
  updateTelegram: (data) => request('/api/config/telegram', { method: 'PUT', body: JSON.stringify(data) }),
  updateAccounts: (data) => request('/api/config/accounts', { method: 'PUT', body: JSON.stringify(data) }),
  updateScheduler: (data) => request('/api/config/scheduler', { method: 'PUT', body: JSON.stringify(data) }),
  testSmtp: () => request('/api/test/smtp', { method: 'POST' }),
  testTelegram: () => request('/api/test/telegram', { method: 'POST' }),
  discoverSystems: (index) => request(`/api/accounts/${index}/discover`, { method: 'POST' }),
  getDiscoveredSystems: (index) => request(`/api/accounts/${index}/systems`),
  updateMonitoredSystems: (index, sids) => request(`/api/accounts/${index}/systems`, { method: 'PUT', body: JSON.stringify({ sids }) }),
  manualReport: () => request('/api/report/manual', { method: 'POST' }),
  triggerCheck: () => request('/api/check', { method: 'POST' }),
  logs: (lines = 100) => request(`/api/logs?lines=${lines}`),
  clearLogs: () => request('/api/logs', { method: 'DELETE' }),
};
