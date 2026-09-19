/**
 * NEURO_PREDICT_SYS — Clerk Authentication Bridge
 *
 * Handles Clerk initialization, auth state, and bridges Clerk sessions
 * with the FastAPI backend for API calls.
 *
 * Usage in HTML files:
 *   <script src="https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js"></script>
 *   <script src="../shared/clerk-init.js"></script>
 *   <script>
 *     ClerkAuth.ready().then(() => {
 *       if (!ClerkAuth.isSignedIn()) { redirect to login }
 *     });
 *   </script>
 */
const ClerkAuth = (() => {
  const CLERK_PUBLISHABLE_KEY = window.__CLERK_PUBLISHABLE_KEY || '';
  const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

  let _clerk = null;
  let _ready = null;

  // ── Resolve relative path from current page to project root ──
  function _getRelativePath(target) {
    const parts = window.location.pathname.split('/').filter(Boolean);
    // Count how deep we are (e.g. /3fa_pharmacy_login/code.html => depth 2)
    const depth = parts.length - 1; // subtract code.html
    const prefix = '../'.repeat(depth);
    return prefix + target;
  }

  // ── Initialize Clerk ──────────────────────────────────────────
  function init() {
    if (_ready) return _ready;

    _ready = new Promise(async (resolve) => {
      // If Clerk script not loaded yet, wait for it
      if (typeof window.Clerk === 'undefined') {
        console.warn('[ClerkAuth] Clerk SDK not loaded. Waiting...');
        // Clerk SDK not available - resolve with fallback
        resolve(false);
        return;
      }

      try {
        _clerk = window.Clerk;
        await _clerk.load({
          publishableKey: CLERK_PUBLISHABLE_KEY,
          appearance: {
            elements: {
              rootBox: { width: '100%' },
              card: {
                background: 'rgba(20,20,34,0.9)',
                backdropFilter: 'blur(16px)',
                border: '1px solid rgba(255,45,120,0.3)',
                boxShadow: '0 0 24px rgba(255,45,120,0.1), inset 0 0 12px rgba(255,45,120,0.05)',
                borderRadius: '0.5rem',
              },
              formButtonPrimary: {
                background: '#ff2d78',
                color: '#1a0010',
                fontFamily: 'Sora, sans-serif',
                fontWeight: 700,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                fontSize: '0.75rem',
                border: 'none',
                boxShadow: '0 0 16px rgba(255,45,120,0.4)',
              },
              formButtonPrimary__hover: {
                background: '#ff5090',
                boxShadow: '0 0 24px rgba(255,45,120,0.6)',
              },
              formFieldInput: {
                background: '#111118',
                border: '1px solid #302840',
                borderRadius: '0.25rem',
                color: '#e8e0f0',
                fontFamily: 'Space Grotesk, monospace',
                fontSize: '0.8rem',
              },
              formFieldInput__focus: {
                border: '1px solid #ff2d78',
                boxShadow: '0 0 12px rgba(255,45,120,0.15)',
              },
              formFieldLabel: {
                color: '#00ffcc',
                fontFamily: 'Space Grotesk, monospace',
                fontSize: '0.65rem',
                letterSpacing: '0.15em',
                textTransform: 'uppercase',
              },
              headerTitle: {
                color: '#ff2d78',
                fontFamily: 'Sora, sans-serif',
                fontWeight: 800,
                textShadow: '0 0 8px rgba(255,45,120,0.8)',
              },
              headerSubtitle: {
                color: '#a098b0',
                fontFamily: 'Space Grotesk, monospace',
                fontSize: '0.7rem',
              },
              socialButtonsBlockButton: {
                background: '#141422',
                border: '1px solid #302840',
                color: '#e8e0f0',
                fontFamily: 'Space Grotesk, monospace',
                fontSize: '0.75rem',
              },
              dividerLine: {
                background: '#302840',
              },
              dividerText: {
                color: '#5a5068',
              },
              footerActionLink: {
                color: '#00ffcc',
              },
            },
            variables: {
              colorPrimary: '#ff2d78',
              colorSecondary: '#00ffcc',
              colorBackground: '#0a0a12',
              colorText: '#e8e0f0',
              colorTextSecondary: '#a098b0',
              borderRadius: '0.25rem',
              fontFamily: 'Inter, sans-serif',
            },
          },
        });
        console.log('[ClerkAuth] Clerk initialized successfully');
        resolve(true);
      } catch (err) {
        console.error('[ClerkAuth] Clerk initialization failed:', err);
        resolve(false);
      }
    });

    return _ready;
  }

  // ── Auth State ────────────────────────────────────────────────
  function isSignedIn() {
    return _clerk && _clerk.user != null;
  }

  function getUser() {
    if (!_clerk || !_clerk.user) return null;
    const u = _clerk.user;
    return {
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
  }

  async function getSessionToken() {
    if (!_clerk || !_clerk.session) return null;
    try {
      return await _clerk.session.getToken();
    } catch {
      return null;
    }
  }

  // ── Redirect Helpers ──────────────────────────────────────────
  function getReturnUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('redirect_url') || '';
  }

  function getCurrentPagePath() {
    return window.location.pathname;
  }

  function buildLoginUrl() {
    const loginPage = _getRelativePath('login/index.html');
    const currentPath = getCurrentPagePath();
    // Don't add redirect if already on login page
    if (currentPath.includes('login/index')) return loginPage;
    return loginPage + '?redirect_url=' + encodeURIComponent(currentPath);
  }

  function redirectToLogin() {
    window.location.href = buildLoginUrl();
  }

  function redirectToIntended() {
    const returnUrl = getReturnUrl();
    if (returnUrl && returnUrl !== getCurrentPagePath()) {
      window.location.href = returnUrl;
    } else {
      // Default redirect after login: dashboard
      window.location.href = _getRelativePath('global_neural_dashboard_v1/code.html');
    }
  }

  function redirectToLanding() {
    window.location.href = _getRelativePath('index.html');
  }

  // ── Mount Clerk Components ────────────────────────────────────
  function mountSignIn(containerId, options = {}) {
    if (!_clerk) return false;
    const container = document.getElementById(containerId);
    if (!container) {
      console.error('[ClerkAuth] Container not found:', containerId);
      return false;
    }
    _clerk.mountSignIn(container, {
      routing: 'hash',
      appearance: options.appearance || {},
      ...options,
    });
    return true;
  }

  function mountSignUp(containerId, options = {}) {
    if (!_clerk) return false;
    const container = document.getElementById(containerId);
    if (!container) return false;
    _clerk.mountSignUp(container, {
      routing: 'hash',
      ...options,
    });
    return true;
  }

  function mountUserButton(containerId, options = {}) {
    if (!_clerk) return false;
    const container = document.getElementById(containerId);
    if (!container) return false;
    _clerk.mountUserButton(container, {
      routing: 'hash',
      appearance: {
        elements: {
          avatarBox: {
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            border: '1px solid rgba(255,45,120,0.5)',
            boxShadow: '0 0 8px rgba(255,45,120,0.3)',
          },
          userButtonPopoverCard: {
            background: '#141422',
            border: '1px solid rgba(255,45,120,0.3)',
            boxShadow: '0 0 24px rgba(255,45,120,0.15)',
          },
          userButtonPopoverActionButton: {
            color: '#e8e0f0',
            fontFamily: 'Space Grotesk, monospace',
            fontSize: '0.75rem',
          },
          userButtonPopoverActionButton__signOut: {
            color: '#ff4444',
          },
        },
      },
      ...options,
    });
    return true;
  }

  // ── Auth Guard (async) ────────────────────────────────────────
  async function requireAuth() {
    await init();
    if (!isSignedIn()) {
      redirectToLogin();
      return false;
    }
    return true;
  }

  // ── Backend Token Bridge ──────────────────────────────────────
  async function syncWithBackend() {
    const token = await getSessionToken();
    if (!token) return null;

    // Store Clerk token for API calls
    localStorage.setItem('neuro_clerk_token', token);

    // Try to get/create user in backend
    try {
      const res = await fetch(`${API_BASE}/auth/clerk-sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          clerk_user_id: getUser()?.id,
          email: getUser()?.email,
          full_name: getUser()?.full_name,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('neuro_token', data.access_token);
        localStorage.setItem('neuro_user', JSON.stringify(data.user));
        return data;
      }
    } catch (err) {
      console.warn('[ClerkAuth] Backend sync failed, using Clerk session only:', err);
    }

    // Fallback: store Clerk user info locally
    const user = getUser();
    if (user) {
      localStorage.setItem('neuro_user', JSON.stringify(user));
    }
    return null;
  }

  // ── Sign Out ──────────────────────────────────────────────────
  async function signOut() {
    if (_clerk) {
      await _clerk.signOut();
    }
    localStorage.removeItem('neuro_token');
    localStorage.removeItem('neuro_user');
    localStorage.removeItem('neuro_clerk_token');
    redirectToLanding();
  }

  // ── Public API ────────────────────────────────────────────────
  return {
    init,
    ready: () => _ready || init(),
    isSignedIn,
    getUser,
    getSessionToken,
    syncWithBackend,
    signOut,
    requireAuth,
    mountSignIn,
    mountSignUp,
    mountUserButton,
    buildLoginUrl,
    redirectToLogin,
    redirectToIntended,
    redirectToLanding,
    getReturnUrl,
    get API_BASE() { return API_BASE; },
  };
})();
