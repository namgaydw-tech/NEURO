/**
 * NEURO_PREDICT_SYS — Profile Panel
 *
 * UI component that reads user state from Auth module.
 * No auth logic, no API calls, no state ownership.
 */
const ProfilePanel = (() => {
  const PORTALS = [
    { name: 'Dashboard',         icon: 'dashboard',        path: '../global_neural_dashboard_v1/code.html',  color: '#ff2d78' },
    { name: 'Neural Archive',    icon: 'psychology',       path: '../neural_archive_eeg_interpreter/code.html', color: '#00ffcc' },
    { name: 'AI Analysis',       icon: 'neurology',        path: '../ai_analysis/code.html',                  color: '#ff2d78' },
    { name: 'Prediction Center', icon: 'monitoring',       path: '../prediction_command_center_v1/code.html',  color: '#00ffcc' },
    { name: 'Research Papers',   icon: 'science',          path: '../research_papers_1/code.html',            color: '#ffe04a' },
    { name: 'Diagnosis Report',  icon: 'assignment',       path: '../final_diagnosis_report_v1/code.html',    color: '#ff2d78' },
    { name: 'Pharmacy',          icon: 'local_pharmacy',   path: '../pharmacist_login/code.html',             color: '#00ffcc' },
    { name: 'Neurosurgery',      icon: 'biotech',          path: '../neurosurgery_login/code.html',           color: '#ffe04a' },
    { name: 'Medical History',   icon: 'folder',           path: '../medical_history_login/code.html',        color: '#ff2d78' },
    { name: 'OT Scheduling',     icon: 'calendar_month',   path: '../ot_scheduling_login/code.html',          color: '#00ffcc' },
  ];

  let _isOpen = false;
  let _panelEl = null;
  let _dropdownEl = null;
  let _mounted = false;

  function _getCurrentPage() {
    return window.location.pathname;
  }

  function _triggerHTML(user) {
    if (user) {
      const tag = user.image_url
        ? `<img src="${user.image_url}" alt="${user.full_name}">`
        : UI.initials(user.full_name);
      return `
        <div class="pp-avatar">${tag}</div>
        <div class="pp-info">
          <div class="pp-name">${user.full_name || 'User'}</div>
          <div class="pp-email">${user.email || user.department || ''}</div>
        </div>
        <span class="material-symbols-outlined pp-chevron">expand_more</span>
      `;
    }
    return `
      <div class="pp-avatar">?</div>
      <div class="pp-info">
        <div class="pp-signin-text">Sign In</div>
        <div class="pp-email">Access your account</div>
      </div>
      <span class="material-symbols-outlined pp-chevron">expand_more</span>
    `;
  }

  function _dropdownHTML(user) {
    const current = _getCurrentPage();
    const loginUrl = Auth.redirectToLogin.toString().includes('return')
      ? Auth.redirectToLogin.toString()
      : '../3fa_pharmacy_login/code.html';

    const header = user ? (() => {
      const tag = user.image_url
        ? `<img src="${user.image_url}" alt="${user.full_name}">`
        : UI.initials(user.full_name);
      return `
        <div class="pp-dropdown-header">
          <div class="pp-dropdown-avatar">${tag}</div>
          <div class="pp-dropdown-user">
            <div class="pp-dropdown-name">${user.full_name || 'User'}</div>
            <div class="pp-dropdown-email">${user.email || ''}</div>
            <div class="pp-dropdown-role">${user.role || 'user'}${user.department ? ' · ' + user.department : ''}</div>
          </div>
        </div>
      `;
    })() : `
      <div class="pp-dropdown-header" style="justify-content:center;text-align:center;">
        <div>
          <div style="font-family:'Sora',sans-serif;font-size:14px;font-weight:700;color:#e8e0f0;margin-bottom:4px;">Not Signed In</div>
          <div style="font-family:'Space Grotesk',monospace;font-size:11px;color:#a098b0;">Sign in to access all features</div>
        </div>
      </div>
    `;

    const links = PORTALS.map(p => {
      const active = current.includes(p.path.replace('../', '').replace('/code.html', ''));
      return `
        <a href="${p.path}" class="pp-portal-link${active ? ' active' : ''}">
          <span class="material-symbols-outlined pp-portal-icon" style="color:${p.color}">${p.icon}</span>
          ${p.name}
          ${active ? '<span class="pp-portal-badge" style="background:rgba(255,45,120,0.2);color:#ff2d78;">ACTIVE</span>' : ''}
        </a>
      `;
    }).join('');

    const action = user
      ? `<button class="pp-signout-btn" onclick="Auth.signOut()">
           <span class="material-symbols-outlined" style="font-size:16px">logout</span>
           Sign Out
         </button>`
      : `<button class="pp-signin-btn" onclick="Auth.redirectToLogin()">
           <span class="material-symbols-outlined" style="font-size:16px">login</span>
           Sign In
         </button>`;

    return `${header}<div class="pp-section-label">Portals</div>${links}<div class="pp-divider"></div>${action}`;
  }

  function _toggle() {
    _isOpen = !_isOpen;
    _dropdownEl?.classList.toggle('visible', _isOpen);
    _panelEl?.querySelector('.pp-chevron')?.classList.toggle('open', _isOpen);
  }

  function _close() {
    _isOpen = false;
    _dropdownEl?.classList.remove('visible');
    _panelEl?.querySelector('.pp-chevron')?.classList.remove('open');
  }

  function _onClickOutside(e) {
    if (_panelEl && !_panelEl.contains(e.target) && _dropdownEl && !_dropdownEl.contains(e.target)) {
      _close();
    }
  }

  // ── Public ───────────────────────────────────────────────────
  function mountInto(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Only create once
    if (_mounted) {
      _render();
      container.appendChild(_panelEl);
      return;
    }

    _panelEl = document.createElement('div');
    _panelEl.className = 'pp-trigger';
    _panelEl.setAttribute('role', 'button');
    _panelEl.setAttribute('tabindex', '0');
    _panelEl.addEventListener('click', _toggle);
    _panelEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); _toggle(); }
    });

    _dropdownEl = document.createElement('div');
    _dropdownEl.className = 'pp-dropdown';
    document.body.appendChild(_dropdownEl);
    document.addEventListener('click', _onClickOutside);

    _mounted = true;
    _render();
    container.appendChild(_panelEl);
  }

  function _render() {
    const user = Auth.getUser();
    _panelEl.innerHTML = _triggerHTML(user);
    _dropdownEl.innerHTML = _dropdownHTML(user);
  }

  function refresh() {
    if (_mounted) _render();
  }

  return { mountInto, refresh };
})();
