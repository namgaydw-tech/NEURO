/**
 * NEURO_PREDICT_SYS — Shared API Client & Utilities
 * Include this script in every module: <script src="../shared/neuro-api.js"></script>
 */
const NeuroAPI = (() => {
  const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

  // ── Clerk Integration ────────────────────────────────────────
  function isClerkAvailable() {
    return typeof window.ClerkAuth !== 'undefined';
  }

  function isClerkSignedIn() {
    return isClerkAvailable() && window.ClerkAuth.isSignedIn();
  }

  // ── Token Management ──────────────────────────────────────────
  function getToken() {
    return localStorage.getItem('neuro_token');
  }

  function setToken(token) {
    localStorage.setItem('neuro_token', token);
  }

  function clearToken() {
    localStorage.removeItem('neuro_token');
    localStorage.removeItem('neuro_user');
  }

  function getUser() {
    try {
      return JSON.parse(localStorage.getItem('neuro_user'));
    } catch {
      return null;
    }
  }

  function setUser(user) {
    localStorage.setItem('neuro_user', JSON.stringify(user));
  }

  function isAuthenticated() {
    // Check Clerk first, then fallback to legacy token
    if (isClerkSignedIn()) return true;
    return !!getToken();
  }

  // ── Auth API ──────────────────────────────────────────────────
  async function login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setToken(data.access_token);
    setUser(data.user);
    return data;
  }

  async function register(userData) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    setToken(data.access_token);
    setUser(data.user);
    return data;
  }

  async function getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error('Unauthorized');
    return res.json();
  }

  async function getDemoAccounts() {
    const res = await fetch(`${API_BASE}/auth/demo-accounts`);
    return res.json();
  }

  // ── Generic Fetch Helper ──────────────────────────────────────
  async function apiFetch(path, options = {}) {
    // Prefer Clerk session token, fallback to legacy JWT
    let token = getToken();
    if (isClerkAvailable() && window.ClerkAuth.isSignedIn()) {
      const clerkToken = await window.ClerkAuth.getSessionToken();
      if (clerkToken) token = clerkToken;
    }
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      clearToken();
      window.location.href = '../3fa_pharmacy_login/code.html';
      throw new Error('Session expired');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  }

  // ── Patient API ───────────────────────────────────────────────
  async function getPatients(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/patients${qs ? '?' + qs : ''}`);
  }

  async function getPatient(id) {
    return apiFetch(`/patients/${id}`);
  }

  async function createPatient(data) {
    return apiFetch('/patients', { method: 'POST', body: JSON.stringify(data) });
  }

  // ── Diagnosis API ─────────────────────────────────────────────
  async function getDiagnoses(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/diagnoses${qs ? '?' + qs : ''}`);
  }

  async function createDiagnosis(data) {
    return apiFetch('/diagnoses', { method: 'POST', body: JSON.stringify(data) });
  }

  // ── Analysis API ──────────────────────────────────────────────
  async function runPrediction(data) {
    return apiFetch('/analysis/predict', { method: 'POST', body: JSON.stringify(data) });
  }

  async function getPatientAnalyses(patientId) {
    return apiFetch(`/analysis/patient/${patientId}`);
  }

  // ── EEG API ───────────────────────────────────────────────────
  async function getPatientEEG(patientId) {
    return apiFetch(`/eeg/patient/${patientId}`);
  }

  async function recordEEG(data) {
    return apiFetch('/eeg/record', { method: 'POST', body: JSON.stringify(data) });
  }

  // ── Research API ──────────────────────────────────────────────
  async function getResearch(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/research${qs ? '?' + qs : ''}`);
  }

  // ── Medication API ────────────────────────────────────────────
  async function getMedications(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/medications${qs ? '?' + qs : ''}`);
  }

  // ── Dashboard API ─────────────────────────────────────────────
  async function getDashboardStats() {
    return apiFetch('/dashboard/stats');
  }

  async function getDashboardActivity() {
    return apiFetch('/dashboard/activity');
  }

  // ── UI Utilities ──────────────────────────────────────────────

  /** Show a toast notification */
  function showToast(message, type = 'info') {
    const colors = {
      info: 'border-secondary text-secondary',
      success: 'border-green-500 text-green-400',
      error: 'border-primary text-primary',
      warning: 'border-tertiary text-tertiary',
    };
    const icons = {
      info: 'info',
      success: 'check_circle',
      error: 'error',
      warning: 'warning',
    };
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

  /** Show loading spinner on an element */
  function showLoading(element) {
    const original = element.innerHTML;
    element.dataset.originalContent = original;
    element.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span>';
    element.disabled = true;
    return () => {
      element.innerHTML = element.dataset.originalContent;
      element.disabled = false;
    };
  }

  /** Update user info in header if present */
  function updateUserHeader() {
    const user = getUser();
    if (!user) return;
    const nameEls = document.querySelectorAll('[data-user-name]');
    nameEls.forEach(el => el.textContent = user.full_name || user.email);
    const roleEls = document.querySelectorAll('[data-user-role]');
    roleEls.forEach(el => el.textContent = user.role?.toUpperCase() || 'USER');
    const deptEls = document.querySelectorAll('[data-user-dept]');
    deptEls.forEach(el => el.textContent = user.department || 'System');
  }

  /** Format date string */
  function formatDate(isoString) {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  }

  /** Format confidence score as percentage */
  function formatConfidence(score) {
    return (score * 100).toFixed(1) + '%';
  }

  /** Get risk level color */
  function getRiskColor(level) {
    const colors = {
      low: 'text-green-400 bg-green-400/10 border-green-400/30',
      medium: 'text-tertiary bg-tertiary/10 border-tertiary/30',
      high: 'text-primary bg-primary/10 border-primary/30',
      critical: 'text-red-500 bg-red-500/10 border-red-500/30',
    };
    return colors[level] || colors.low;
  }

  // ── Auth Guard ────────────────────────────────────────────────
  function requireAuth() {
    // Check Clerk first
    if (isClerkAvailable() && window.ClerkAuth.isSignedIn()) {
      updateUserHeader();
      return true;
    }
    // Fallback to legacy token
    if (isAuthenticated()) {
      updateUserHeader();
      return true;
    }
    // Not authenticated - redirect to login with return URL
    const currentPath = window.location.pathname;
    window.location.href = '../3fa_pharmacy_login/code.html?redirect_url=' + encodeURIComponent(currentPath);
    return false;
  }

  // ── Logout ────────────────────────────────────────────────────
  async function logout() {
    // Sign out from Clerk if available
    if (isClerkAvailable()) {
      await window.ClerkAuth.signOut();
      return; // signOut handles redirect
    }
    clearToken();
    window.location.href = '../index.html';
  }

  // Public API
  return {
    login, register, getMe, getDemoAccounts, logout,
    getToken, getUser, isAuthenticated, requireAuth,
    isClerkSignedIn, isClerkAvailable,
    getPatients, getPatient, createPatient,
    getDiagnoses, createDiagnosis,
    runPrediction, getPatientAnalyses,
    getPatientEEG, recordEEG,
    getResearch, getMedications,
    getDashboardStats, getDashboardActivity,
    showToast, showLoading, updateUserHeader,
    formatDate, formatConfidence, getRiskColor,
  };
})();
