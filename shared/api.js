/**
 * NEURO_PREDICT_SYS — API Client
 *
 * Pure HTTP client for all backend endpoints.
 * No auth state, no UI helpers, no redirects.
 * Uses Auth module for token injection.
 */
const Api = (() => {
  const BASE = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

  // ── Generic fetch with auto-auth ─────────────────────────────
  async function request(path, options = {}) {
    const token = await Auth.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };
    const res = await fetch(`${BASE}${path}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  }

  function _qs(params) {
    const s = new URLSearchParams(params).toString();
    return s ? '?' + s : '';
  }

  // ── Auth endpoints (legacy) ──────────────────────────────────
  const auth = {
    register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    me: () => request('/auth/me'),
    demoAccounts: () => request('/auth/demo-accounts'),
  };

  // ── Patients ─────────────────────────────────────────────────
  const patients = {
    list: (params = {}) => request('/patients' + _qs(params)),
    get: (id) => request(`/patients/${id}`),
    create: (data) => request('/patients', { method: 'POST', body: JSON.stringify(data) }),
  };

  // ── Diagnoses ────────────────────────────────────────────────
  const diagnoses = {
    list: (params = {}) => request('/diagnoses' + _qs(params)),
    create: (data) => request('/diagnoses', { method: 'POST', body: JSON.stringify(data) }),
  };

  // ── AI Analysis / Prediction ─────────────────────────────────
  const analysis = {
    predict: (data) => request('/analysis/predict', { method: 'POST', body: JSON.stringify(data) }),
    byPatient: (patientId) => request(`/analysis/patient/${patientId}`),
  };

  // ── EEG ──────────────────────────────────────────────────────
  const eeg = {
    byPatient: (patientId) => request(`/eeg/patient/${patientId}`),
    record: (data) => request('/eeg/record', { method: 'POST', body: JSON.stringify(data) }),
  };

  // ── Research ─────────────────────────────────────────────────
  const research = {
    list: (params = {}) => request('/research' + _qs(params)),
  };

  // ── Medications ──────────────────────────────────────────────
  const medications = {
    list: (params = {}) => request('/medications' + _qs(params)),
  };

  // ── Dashboard ────────────────────────────────────────────────
  const dashboard = {
    stats: () => request('/dashboard/stats'),
    activity: () => request('/dashboard/activity'),
  };

  return { request, auth, patients, diagnoses, analysis, eeg, research, medications, dashboard };
})();
