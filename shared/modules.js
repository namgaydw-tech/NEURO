/**
 * NEURO_PREDICT_SYS — Role-Based Module Access Map
 *
 * Single source of truth for which UI modules each role can see.
 * This is UX-level filtering only — the FastAPI backend enforces real
 * authorization on every endpoint. Hiding a link here is not security.
 *
 * Usage: call Modules.init('moduleKey') once per page. It handles:
 *   - Auth guard (redirects to login if unauthenticated)
 *   - Module guard (redirects to dashboard if role lacks access — fail-open if modules.js broken)
 *   - Desktop nav rendering (into #desktop-nav or first <nav> in header)
 *   - Mobile nav rendering (into #mobile-nav)
 *   - Profile panel mounting (into #profile-panel-trigger)
 */
const Modules = (() => {
  // ── Module definitions ──────────────────────────────────────
  const MODULES = {
    dashboard: {
      label: 'Dashboard', shortLabel: 'Home', icon: 'grid_view',
      path: '/global_neural_dashboard_v1/code.html',
      roles: 'all', // every signed-in role
    },
    patients: {
      label: 'Patients', shortLabel: 'Patients', icon: 'groups',
      path: '/neurosurgery/index.html',
      roles: ['admin', 'neurologist', 'neurosurgeon', 'surgeon', 'radiologist',
              'nurse', 'clinical_staff', 'anesthesiologist', 'pharmacist'],
    },
    analysis: {
      label: 'AI Analysis', shortLabel: 'Analysis', icon: 'analytics',
      path: '/ai_analysis/code.html',
      roles: ['admin', 'neurologist', 'researcher'],
    },
    eeg: {
      label: 'EEG Archive', shortLabel: 'EEG', icon: 'database',
      path: '/neural_archive_eeg_interpreter/code.html',
      roles: ['admin', 'neurologist', 'pharmacist'],
    },
    ot: {
      label: 'OT Scheduling', shortLabel: 'OT', icon: 'event_available',
      path: '/ot_scheduling/index.html',
      roles: ['admin', 'neurosurgeon', 'surgeon', 'ot_coordinator',
              'anesthesiologist', 'nurse'],
    },
    neurosurgery: {
      label: 'Neurosurgery', shortLabel: 'Neuro', icon: 'neurology',
      path: '/neurosurgery/index.html',
      roles: ['admin', 'neurosurgeon', 'surgeon', 'ot_coordinator',
              'anesthesiologist', 'nurse', 'neurologist'],
    },
    research: {
      label: 'Research', shortLabel: 'Research', icon: 'science',
      path: '/research_papers_1/code.html',
      roles: ['admin', 'neurologist', 'neurosurgeon', 'surgeon', 'researcher',
              'radiologist'],
    },
  };

  // ── Resolve user role ───────────────────────────────────────
  function currentRole() {
    try {
      const user = (typeof Auth !== 'undefined' && Auth && Auth.getUser)
        ? Auth.getUser()
        : null;
      return user ? (user.role || 'demo') : null;
    } catch (_) {
      return null;
    }
  }

  // ── Can this role see a module? ─────────────────────────────
  function canSee(moduleKey, role) {
    const mod = MODULES[moduleKey];
    if (!mod) return false;
    const r = role || currentRole();
    if (!r) return false;
    if (mod.roles === 'all') return true;
    return mod.roles.includes(r);
  }

  // ── Ordered list of modules visible to a role ───────────────
  function forRole(role) {
    const r = role || currentRole();
    return Object.keys(MODULES).filter(key => canSee(key, r)).map(key => ({
      key,
      ...MODULES[key],
    }));
  }

  // ── Find desktop nav container by ID, then by convention ────
  function _findDesktopNav() {
    // 1. Prefer explicit ID (most robust)
    const byId = document.getElementById('desktop-nav');
    if (byId) return byId;
    // 2. <header> with nested <nav> (dashboard pattern)
    const header = document.querySelector('header');
    if (header) {
      const rightSide = header.querySelector('.hidden.md\\:flex, .ml-auto');
      if (rightSide) {
        const nav = rightSide.querySelector('nav');
        if (nav) return nav;
      }
    }
    // 3. <nav> as top bar with .ml-auto container (ai_analysis, eeg, research pattern)
    const topNav = document.querySelector('nav.fixed, nav[class*="top-0"]');
    if (topNav) {
      const rightSide = topNav.querySelector('.ml-auto');
      if (rightSide) return rightSide;
    }
    return null;
  }

  // ── Find mobile nav container ───────────────────────────────
  function _findMobileNav() {
    return document.getElementById('mobile-nav');
  }

  // ── Render desktop nav links ────────────────────────────────
  function renderDesktopNav(container, activeKey) {
    if (!container) return;
    const items = forRole();
    container.innerHTML = items.map(m => {
      const active = m.key === activeKey;
      return `<a class="font-label text-sm uppercase tracking-widest ${
        active
          ? 'text-[#00ffcc] drop-shadow-[0_0_8px_rgba(0,255,204,0.8)] font-bold'
          : 'text-slate-400 hover:text-[#ff2d78]'
      } transition-all duration-300" href="${m.path}">${m.label}</a>`;
    }).join('');
  }

  // ── Render mobile bottom nav ────────────────────────────────
  function renderMobileNav(container, activeKey) {
    if (!container) return;
    const items = forRole();
    container.innerHTML = items.map(m => {
      const active = m.key === activeKey;
      return `<a class="flex flex-col items-center justify-center ${
        active
          ? 'text-[#ff2d78] drop-shadow-[0_0_10px_rgba(255,45,120,0.6)] font-bold'
          : 'text-slate-500 hover:bg-white/5'
      } transition-colors active:scale-90 duration-150" href="${m.path}">
        <span class="material-symbols-outlined" data-icon="${m.icon}">${m.icon}</span>
        <span class="font-['Space_Grotesk'] text-[10px] uppercase tracking-widest mt-1">${m.shortLabel}</span>
      </a>`;
    }).join('');
  }

  // ── Guard: fail-open if modules.js is broken ────────────────
  // Returns true if access is allowed, false if redirected.
  // If role cannot be determined (Auth not loaded, etc.), allows access
  // because the backend enforces real security anyway.
  function requireModule(moduleKey) {
    const role = currentRole();
    // If we can't determine the role, fail OPEN — the backend is the
    // real security boundary. Bricking the UI because modules.js
    // loaded before auth.js is worse than letting a logged-in user
    // see a page the backend will reject.
    if (!role) return true;
    if (canSee(moduleKey, role)) return true;
    // Not permitted — redirect to dashboard
    try {
      window.location.replace(MODULES.dashboard.path);
    } catch (_) {
      // If replace fails (e.g., same origin), just navigate
      window.location.href = MODULES.dashboard.path;
    }
    return false;
  }

  // ── Mount profile panel if available ────────────────────────
  function _mountProfile() {
    try {
      if (typeof ProfilePanel !== 'undefined' && ProfilePanel.mountInto) {
        ProfilePanel.mountInto('profile-panel-trigger');
        ProfilePanel.mountInto('profile-panel-trigger-mobile');
      }
    } catch (_) {
      // Profile panel is optional — don't break the page if it fails
    }
  }

  // ── Single init call per page ───────────────────────────────
  // Does everything: guard, nav render, profile mount.
  // Pages call: await Auth.ready(); if (!Auth.requireAuth()) return; Modules.init('analysis');
  function init(moduleKey) {
    // 1. Module guard (fail-open)
    if (moduleKey && !requireModule(moduleKey)) return false;

    // 2. Desktop nav (auto-find container)
    const desktopNav = _findDesktopNav();
    if (desktopNav) renderDesktopNav(desktopNav, moduleKey || 'dashboard');

    // 3. Mobile nav (auto-find container)
    const mobileNav = _findMobileNav();
    if (mobileNav) renderMobileNav(mobileNav, moduleKey || 'dashboard');

    // 4. Profile panel (optional, fail-safe)
    _mountProfile();

    return true;
  }

  return {
    MODULES,
    currentRole,
    canSee,
    forRole,
    renderDesktopNav,
    renderMobileNav,
    requireModule,
    init,
  };
})();
