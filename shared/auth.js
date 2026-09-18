/**
 * NEURO_PREDICT_SYS — Auth Module
 *
 * Single owner of authentication state. Merges Clerk (when configured)
 * with legacy JWT fallback. Every other module reads auth from here.
 *
 * Usage:
 *   await Auth.ready();
 *   if (Auth.isSignedIn()) { ... }
 *   Auth.requireAuth();  // redirects if not signed in
 */
const Auth = (() => {
  const LOGIN_PATH = '../3fa_pharmacy_login/code.html';
  const DASHBOARD_PATH = '../global_neural_dashboard_v1/code.html';
  const LANDING_PATH = '../index.html';

  let _user = null;
  let _token = null;
  let _ready = null;
  let _source = null; // 'clerk' | 'jwt' | null

  // ── Path resolution ──────────────────────────────────────────
  function _rel(target) {
    const depth = window.location.pathname.split('/').filter(Boolean).length - 1;
    return '../'.repeat(depth) + target;
  }

  // ── Resolve user from whichever auth source is active ─────────
  function _resolveUser() {
    // 1. Try Clerk
    if (typeof window.Clerk !== 'undefined' && window.Clerk.user) {
      const u = window.Clerk.user;
      _user = {
        id: u.id,
        email: u.emailAddresses?.[0]?.emailAddress || '',
        full_name: [u.firstName, u.lastName].filter(Boolean).join(' ') || u.emailAddresses?.[0]?.emailAddress || 'User',
        first_name: u.firstName || '',
        last_name: u.lastName || '',
        image_url: u.imageUrl || '',
        role: 'user',
        department: null,
        clearance_level: 1,
      };
      _source = 'clerk';
      return;
    }
    // 2. Try legacy JWT
    const stored = localStorage.getItem('neuro_user');
    if (stored) {
      try {
        _user = JSON.parse(stored);
        _source = 'jwt';
        return;
      } catch {}
    }
    _user = null;
    _source = null;
  }

  // ── Token getter ─────────────────────────────────────────────
  async function _getToken() {
    // Prefer Clerk session token
    if (_source === 'clerk' && window.Clerk?.session) {
      try {
        const t = await window.Clerk.session.getToken();
        if (t) return t;
      } catch {}
    }
    // Fallback to legacy JWT
    return localStorage.getItem('neuro_token') || null;
  }

  // ── Initialization ───────────────────────────────────────────
  function init() {
    if (_ready) return _ready;
    _ready = new Promise(async (resolve) => {
      // Try loading Clerk if SDK is present
      if (typeof window.Clerk !== 'undefined' && window.__CLERK_PUBLISHABLE_KEY) {
        try {
          await window.Clerk.load({ publishableKey: window.__CLERK_PUBLISHABLE_KEY });
          console.log('[Auth] Clerk initialized');
        } catch (e) {
          console.warn('[Auth] Clerk init failed, using legacy:', e.message);
        }
      }
      _resolveUser();
      // Auto-login with demo account if no user is signed in
      if (!_user) {
        try {
          await login('admin@neuropredict.sys', 'admin123');
          console.log('[Auth] Auto-logged in with demo account');
        } catch (e) {
          console.warn('[Auth] Auto-demo-login failed:', e.message);
        }
      }
      resolve(true);
    });
    return _ready;
  }

  // ── Public state ─────────────────────────────────────────────
  function isSignedIn() { return _user !== null; }
  function getUser() { return _user; }
  function getSource() { return _source; }

  // ── Auth guard ───────────────────────────────────────────────
  function requireAuth() {
    if (!isSignedIn()) {
      window.location.href = _rel(LOGIN_PATH) + '?redirect_url=' + encodeURIComponent(window.location.pathname);
      return false;
    }
    return true;
  }

  // ── Redirects ────────────────────────────────────────────────
  function redirectToLogin() {
    window.location.href = _rel(LOGIN_PATH) + '?redirect_url=' + encodeURIComponent(window.location.pathname);
  }

  function redirectToIntended() {
    const params = new URLSearchParams(window.location.search);
    const returnUrl = params.get('redirect_url');
    if (returnUrl && returnUrl !== window.location.pathname) {
      window.location.href = returnUrl;
    } else {
      window.location.href = _rel(DASHBOARD_PATH);
    }
  }

  function redirectToLanding() {
    window.location.href = _rel(LANDING_PATH);
  }

  function getReturnUrl() {
    return new URLSearchParams(window.location.search).get('redirect_url') || '';
  }

  // ── Legacy JWT login ─────────────────────────────────────────
  async function login(email, password) {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
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
    localStorage.setItem('neuro_token', data.access_token);
    localStorage.setItem('neuro_user', JSON.stringify(data.user));
    _user = data.user;
    _source = 'jwt';
    _token = data.access_token;
    return data;
  }

  // ── Sign out ─────────────────────────────────────────────────
  async function signOut() {
    if (_source === 'clerk' && window.Clerk) {
      try { await window.Clerk.signOut(); } catch {}
    }
    localStorage.removeItem('neuro_token');
    localStorage.removeItem('neuro_user');
    localStorage.removeItem('neuro_clerk_token');
    _user = null;
    _token = null;
    _source = null;
    redirectToLanding();
  }

  // ── Refresh (call after login on same page) ──────────────────
  function refresh() {
    _resolveUser();
  }

  // ── Public API ───────────────────────────────────────────────
  return {
    init,
    ready: () => _ready || init(),
    isSignedIn,
    getUser,
    getSource,
    getToken: _getToken,
    requireAuth,
    redirectToLogin,
    redirectToIntended,
    redirectToLanding,
    getReturnUrl,
    login,
    signOut,
    refresh,
  };
})();
