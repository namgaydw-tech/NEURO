// NEURO_PREDICT_SYS — Clerk Configuration
// ================================================================
// IMPORTANT: Replace the empty string below with your Clerk
// publishable key from https://dashboard.clerk.com/ > API Keys
//
// Format: pk_test_... (development) or pk_live_... (production)
//
// When empty, Clerk is not loaded — demo/local JWT auth is used.
// ================================================================
window.__CLERK_PUBLISHABLE_KEY = '';

// Dynamically load Clerk SDK only when a key is configured.
// Without this, the SDK throws a fatal error on every page.
(function _loadClerkIfConfigured() {
  const key = window.__CLERK_PUBLISHABLE_KEY;
  if (!key || key.trim() === '') {
    console.info('[Config] No Clerk publishable key — using legacy JWT auth');
    return;
  }
  const s = document.createElement('script');
  s.src = 'https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js';
  s.async = true;
  s.onerror = function () { console.warn('[Config] Failed to load Clerk SDK'); };
  document.head.appendChild(s);
})();
