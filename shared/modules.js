/**
 * NEURO_PREDICT_SYS — Role-Based Module Access Map
 *
 * Single source of truth for which UI modules each role can see.
 * This is UX-level filtering only — the FastAPI backend enforces real
 * authorization on every endpoint. Hiding a link here is not security.
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
    const user = (typeof Auth !== 'undefined') ? Auth.getUser() : null;
    return user ? (user.role || 'demo') : null;
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

  // ── Render desktop nav links (into <nav> containers) ────────
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

  // ── Guard: call at the top of a module page ─────────────────
  // Redirects to dashboard with a notice if the role lacks access.
  function requireModule(moduleKey) {
    const role = currentRole();
    if (!role) return false; // auth.js handles unauthenticated redirect
    if (canSee(moduleKey, role)) return true;
    // Not permitted — redirect silently
    window.location.replace(MODULES.dashboard.path);
    return false;
  }

  return { MODULES, currentRole, canSee, forRole, renderDesktopNav, renderMobileNav, requireModule };
})();
