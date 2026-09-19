/**
 * NEURO_PREDICT_SYS — Unified API Client
 *
 * Pure HTTP client for all backend endpoints.
 * Auth state lives in Auth module — this injects tokens.
 * No auth logic, no UI helpers, no state ownership.
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

    if (res.status === 401) {
      // Token expired or invalid — redirect to login
      Auth.signOut();
      throw new Error('Session expired');
    }
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

  // ── Auth endpoints (legacy + demo) ──────────────────────────
  const auth = {
    register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    login: (email, password) => request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
    me: () => request('/auth/me'),
    demoAccounts: () => request('/auth/demo-accounts'),
    refresh: (refreshToken) => request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
    demoLogin: (email) => request(`/auth/demo-login?email=${encodeURIComponent(email)}`),
  };

  // ── Patients ─────────────────────────────────────────────────
  const patients = {
    list: (params = {}) => request('/patients' + _qs(params)),
    get: (id) => request(`/patients/${id}`),
    create: (data) => request('/patients', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/patients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => request(`/patients/${id}`, { method: 'DELETE' }),
  };

  // ── Diagnoses ────────────────────────────────────────────────
  const diagnoses = {
    list: (params = {}) => request('/diagnoses' + _qs(params)),
    get: (id) => request(`/diagnoses/${id}`),
    create: (data) => request('/diagnoses', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/diagnoses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  };

  // ── AI Analysis / Prediction ─────────────────────────────────
  const analysis = {
    predict: (data) => request('/analysis/predict', { method: 'POST', body: JSON.stringify(data) }),
    get: (id) => request(`/analysis/${id}`),
    byPatient: (patientId) => request(`/analysis/patient/${patientId}`),
  };

  // ── EEG ──────────────────────────────────────────────────────
  const eeg = {
    byPatient: (patientId) => request(`/eeg/patient/${patientId}`),
    get: (id) => request(`/eeg/${id}`),
    record: (data) => request('/eeg/record', { method: 'POST', body: JSON.stringify(data) }),
  };

  // ── Research ─────────────────────────────────────────────────
  const research = {
    list: (params = {}) => request('/research' + _qs(params)),
    get: (id) => request(`/research/${id}`),
    create: (data) => request('/research', { method: 'POST', body: JSON.stringify(data) }),
  };

  // ── Medications ──────────────────────────────────────────────
  const medications = {
    list: (params = {}) => request('/medications' + _qs(params)),
    get: (id) => request(`/medications/${id}`),
  };

  // ── OT Scheduling ────────────────────────────────────────────
  const ot = {
    theaters: () => request('/ot/theaters'),
    createTheater: (data) => request('/ot/theaters', { method: 'POST', body: JSON.stringify(data) }),
    slots: (params = {}) => request('/ot/slots' + _qs(params)),
    getSlot: (id) => request(`/ot/slots/${id}`),
    createSlot: (data) => request('/ot/slots', { method: 'POST', body: JSON.stringify(data) }),
    updateSlot: (id, data) => request(`/ot/slots/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    bookings: (params = {}) => request('/ot/bookings' + _qs(params)),
    getBooking: (id) => request(`/ot/bookings/${id}`),
    createBooking: (data) => request('/ot/bookings', { method: 'POST', body: JSON.stringify(data) }),
    updateBooking: (id, data) => request(`/ot/bookings/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    cancelBooking: (id) => request(`/ot/bookings/${id}`, { method: 'DELETE' }),
    dailySchedule: (date) => request('/ot/daily-schedule' + _qs({ date })),
  };

  // ── Dashboard ────────────────────────────────────────────────
  const dashboard = {
    stats: () => request('/dashboard/stats'),
    activity: () => request('/dashboard/activity'),
  };

  // ── Pharmacy ─────────────────────────────────────────────────
  const pharmacy = {
    profile: () => request('/pharmacy/profile'),
    createProfile: (data) => request('/pharmacy/profile', { method: 'POST', body: JSON.stringify(data) }),
    updateProfile: (id, data) => request(`/pharmacy/profile/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  };

  // ── User Profile ─────────────────────────────────────────────
  const user = {
    me: () => request('/auth/me'),
    myProfile: () => request('/users/me/profile'),
    updateProfile: (data) => request('/users/me/profile', { method: 'PUT', body: JSON.stringify(data) }),
  };

  // ── System ───────────────────────────────────────────────────
  const system = {
    status: () => request('/system/status'),
  };

  // ── UI Helpers ───────────────────────────────────────────────

  /** Show a toast notification */
  function showToast(message, type = 'info') {
    const colors = {
      info: 'border-secondary text-secondary',
      success: 'border-green-500 text-green-400',
      error: 'border-primary text-primary',
      warning: 'border-tertiary text-tertiary',
    };
    const icons = { info: 'info', success: 'check_circle', error: 'error', warning: 'warning' };
    const toast = document.createElement('div');
    toast.className = `fixed top-20 right-4 z-[100] px-4 py-3 bg-surface-container border ${colors[type]} rounded-lg backdrop-blur-xl shadow-lg flex items-center gap-3 transform translate-x-full transition-transform duration-300`;
    toast.innerHTML = `
      <span class="material-symbols-outlined text-lg">${icons[type]}</span>
      <span class="font-label text-sm">${message}</span>
    `;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.remove('translate-x-full'));
    setTimeout(() => {
      toast.classList.add('translate-x-full');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  /** Format date string */
  function formatDate(isoString) {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
  }

  /** Format confidence score as percentage */
  function formatConfidence(score) {
    return (score * 100).toFixed(1) + '%';
  }

  /** Get risk level color classes */
  function getRiskColor(level) {
    const colors = {
      low: 'text-green-400 bg-green-400/10 border-green-400/30',
      medium: 'text-tertiary bg-tertiary/10 border-tertiary/30',
      high: 'text-primary bg-primary/10 border-primary/30',
      critical: 'text-red-500 bg-red-500/10 border-red-500/30',
    };
    return colors[level] || colors.low;
  }

  // Public API
  return {
    request,
    auth, patients, diagnoses, analysis, eeg, research,
    medications, ot, dashboard, pharmacy, user, system,
    showToast, formatDate, formatConfidence, getRiskColor,
  };
})();
