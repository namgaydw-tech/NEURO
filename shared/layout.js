/**
 * NEURO_PREDICT_SYS — Layout Controller v2
 * Theme, adaptive drawer (focus-trapped), offline banner, page detection.
 * Conventions:
 *  - Drawer open: aria-expanded on trigger, focus moves into sidebar.
 *  - Drawer close: Escape / overlay / nav click → focus returns to trigger.
 *  - Main content is aria-hidden while drawer is open (inert-like).
 */
const Layout = (() => {
  const THEME_KEY = 'neuro_theme';
  const THEME_COLOR = { dark: '#08080f', light: '#f7f6f9' };

  // ── Page detection ────────────────────────────────────────────
  const PAGES = {
    '/': { section: 'home', title: 'Home' },
    '/landing/': { section: 'home', title: 'Home' },
    '/app/': { section: 'dashboard', title: 'Dashboard' },
    '/global_neural_dashboard_v1/': { section: 'dashboard', title: 'Dashboard' },
    '/ai_analysis/': { section: 'analysis', title: 'AI Analysis' },
    '/prediction_command_center_v1/': { section: 'prediction', title: 'Prediction Center' },
    '/final_diagnosis_report_v1/': { section: 'diagnosis', title: 'Diagnosis Report' },
    '/neural_archive_eeg_interpreter/': { section: 'archive', title: 'EEG Archive' },
    '/research_papers_1/': { section: 'research', title: 'Research Papers' },
    '/research_papers_2/': { section: 'research', title: 'Research Papers' },
    '/3fa_pharmacy_login/': { section: 'pharmacy', title: 'Pharmacy' },
    '/pharmacist_login/': { section: 'pharmacy', title: 'Pharmacy' },
    '/ot_scheduling_login/': { section: 'ot', title: 'OT Scheduling' },
    '/neurosurgery_login/': { section: 'surgery', title: 'Neurosurgery' },
    '/medical_history_login/': { section: 'history', title: 'Medical History' },
  };

  function getCurrentPage() {
    const path = window.location.pathname;
    // Longest-prefix match so /app/ doesn't shadow /ai_analysis/ etc.
    const sorted = Object.keys(PAGES).sort((a, b) => b.length - a.length);
    for (const prefix of sorted) {
      if (prefix === '/' ? path === '/' : path.startsWith(prefix)) return PAGES[prefix];
    }
    return { section: 'dashboard', title: 'Dashboard' };
  }

  // ── Theme ─────────────────────────────────────────────────────
  function initTheme() {
    let theme = localStorage.getItem(THEME_KEY);
    if (!theme) {
      // Product defaults to dark; honor a genuine light preference.
      theme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    applyTheme(theme);

    // Follow OS changes only when the user hasn't chosen explicitly.
    window.matchMedia('(prefers-color-scheme: light)')
      .addEventListener?.('change', (e) => {
        if (!localStorage.getItem(THEME_KEY)) applyTheme(e.matches ? 'light' : 'dark');
      });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
    // Sync browser/taskbar chrome + Android status bar via meta.
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'theme-color';
      document.head.appendChild(meta);
    }
    meta.content = THEME_COLOR[theme] || THEME_COLOR.dark;
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(THEME_KEY, next); // explicit choice wins over OS
    applyTheme(next);
    UI?.toast?.(`Switched to ${next} theme`, 'info');
  }

  function updateThemeIcon(theme) {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    btn.innerHTML = theme === 'dark'
      ? '<span class="material-symbols-outlined" aria-hidden="true">light_mode</span>'
      : '<span class="material-symbols-outlined" aria-hidden="true">dark_mode</span>';
    btn.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`);
    btn.setAttribute('aria-pressed', String(theme === 'light'));
  }

  // ── Drawer (focus management) ─────────────────────────────────
  const focusableSel =
    'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';

  function drawerElements() {
    return {
      sidebar: document.querySelector('.sidebar'),
      overlay: document.querySelector('.sidebar-overlay'),
      trigger: document.getElementById('mobileMenuBtn'),
      main: document.querySelector('.main'),
    };
  }

  function isDrawerOpen() {
    return document.querySelector('.sidebar')?.classList.contains('open') ?? false;
  }

  function openDrawer() {
    const { sidebar, overlay, trigger, main } = drawerElements();
    if (!sidebar) return;
    sidebar.classList.add('open');
    overlay?.classList.add('open');
    trigger?.setAttribute('aria-expanded', 'true');
    main?.setAttribute('aria-hidden', 'true');
    const first = sidebar.querySelector(focusableSel);
    first?.focus();
  }

  function closeDrawer({ restoreFocus = true } = {}) {
    const { sidebar, overlay, trigger, main } = drawerElements();
    if (!sidebar?.classList.contains('open')) return;
    sidebar.classList.remove('open');
    overlay?.classList.remove('open');
    trigger?.setAttribute('aria-expanded', 'false');
    main?.removeAttribute('aria-hidden');
    if (restoreFocus) trigger?.focus();
  }

  function toggleSidebar() {
    isDrawerOpen() ? closeDrawer() : openDrawer();
  }

  function trapDrawerFocus(e) {
    if (!isDrawerOpen() || e.key !== 'Tab') return;
    const { sidebar } = drawerElements();
    const items = [...sidebar.querySelectorAll(focusableSel)]
      .filter(el => el.offsetParent !== null);
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  // ── Offline banner ────────────────────────────────────────────
  function initOfflineBanner() {
    let banner = document.getElementById('offlineBanner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'offlineBanner';
      banner.className = 'system-banner';
      banner.hidden = true;
      banner.innerHTML = `
        <div class="banner banner-warning" role="status">
          <span class="material-symbols-outlined" aria-hidden="true">wifi_off</span>
          <div class="banner-text">
            <strong>You're offline.</strong>
            <span> Showing cached data — it will refresh automatically when you reconnect.</span>
          </div>
        </div>`;
      const main = document.querySelector('.main');
      const header = main?.querySelector('.header');
      if (main && header) main.insertBefore(banner, header.nextSibling);
    }
    const update = () => { banner.hidden = navigator.onLine; };
    window.addEventListener('online', () => {
      update();
      UI?.toast?.('Back online', 'success');
      document.dispatchEvent(new CustomEvent('neuro:online'));
    });
    window.addEventListener('offline', update);
    update();
  }

  // ── Active nav item ───────────────────────────────────────────
  function highlightActiveNav() {
    const { section } = getCurrentPage();
    document.querySelectorAll('.nav-item, .mobile-nav-item').forEach(item => {
      const isActive = item.dataset.section === section;
      item.classList.toggle('active', isActive);
      if (isActive) item.setAttribute('aria-current', 'page');
      else item.removeAttribute('aria-current');
    });
  }

  // ── Keyboard shortcuts (additive, never trapping) ─────────────
  function initShortcuts() {
    document.addEventListener('keydown', (e) => {
      const target = e.target;
      const typing = target.closest?.('input, textarea, select, [contenteditable="true"]');
      if (e.key === 'Escape' && isDrawerOpen()) {
        closeDrawer();
        return;
      }
      if (typing) return;
      // "/" focuses search — conventional, discoverable, non-blocking
      if (e.key === '/') {
        const search = document.querySelector('.header-search .input');
        if (search) {
          e.preventDefault();
          search.focus();
        }
      }
    });
  }

  // ── Init ──────────────────────────────────────────────────────
  function init() {
    initTheme();
    highlightActiveNav();
    initOfflineBanner();
    initShortcuts();

    const { trigger, overlay } = drawerElements();
    trigger?.addEventListener('click', toggleSidebar);
    overlay?.addEventListener('click', () => closeDrawer());
    document.addEventListener('keydown', trapDrawerFocus);

    // Theme toggle
    document.getElementById('themeToggle')?.addEventListener('click', toggleTheme);

    // Close drawer after navigating from it (mobile)
    document.querySelectorAll('.sidebar .nav-item').forEach(item => {
      item.addEventListener('click', () => {
        if (window.innerWidth < 1024) closeDrawer({ restoreFocus: false });
      });
    });

    // Close drawer if viewport grows into desktop shell
    window.matchMedia('(min-width: 1024px)').addEventListener?.('change', (e) => {
      if (e.matches) closeDrawer({ restoreFocus: false });
    });
  }

  return { init, toggleTheme, toggleSidebar, closeDrawer, getCurrentPage, isDrawerOpen };
})();

document.addEventListener('DOMContentLoaded', Layout.init);
