/**
 * NEURO_PREDICT_SYS — UI Utilities v2
 * Toasts, escaping, safe DOM building, formatting.
 * Pure presentation helpers. No auth, no API, no state.
 */
const UI = (() => {
  // ── HTML escaping — use for ALL dynamic text ─────────────────
  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/`/g, '&#96;');
  }

  // Build a single element from an HTML string.
  function el(html) {
    const tpl = document.createElement('template');
    tpl.innerHTML = String(html).trim();
    return tpl.content.firstElementChild;
  }

  // ── Toasts ───────────────────────────────────────────────────
  // role=status for success/info (polite), role=alert for error/warning.
  let container = null;

  function ensureContainer() {
    if (container && document.contains(container)) return container;
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
  }

  function toast(message, type = 'info', { timeout = 3500 } = {}) {
    ensureContainer();
    const icons = { info: 'info', success: 'check_circle', error: 'error', warning: 'warning' };
    const role = (type === 'error' || type === 'warning') ? 'alert' : 'status';
    const t = el(
      `<div class="toast toast-${esc(type)}" role="${role}">
        <span class="material-symbols-outlined" aria-hidden="true">${icons[type] || 'info'}</span>
        <div class="toast-message">${esc(message)}</div>
        <button type="button" class="toast-close" aria-label="Dismiss notification">
          <span class="material-symbols-outlined" aria-hidden="true">close</span>
        </button>
      </div>`
    );
    const remove = () => {
      if (!t.isConnected) return;
      t.classList.add('toast-leaving');
      setTimeout(() => t.remove(), 200);
    };
    t.querySelector('.toast-close').addEventListener('click', remove);
    container.appendChild(t);
    const timer = setTimeout(remove, timeout);
    return { remove: () => { clearTimeout(timer); remove(); } };
  }

  // ── Loading helper (buttons) ─────────────────────────────────
  function showLoading(element, loadingText = 'Loading…') {
    const original = element.innerHTML;
    element.innerHTML = `<span class="spinner" aria-hidden="true"></span> ${esc(loadingText)}`;
    element.setAttribute('aria-busy', 'true');
    element.setAttribute('aria-disabled', 'true');
    return () => {
      element.innerHTML = original;
      element.removeAttribute('aria-busy');
      element.removeAttribute('aria-disabled');
    };
  }

  // ── Formatting ───────────────────────────────────────────────
  function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function formatTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '—' : d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  }

  function formatRelative(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '—';
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 45) return 'just now';
    if (diff < 3600) return `${Math.round(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.round(diff / 3600)} h ago`;
    if (diff < 604800) return `${Math.round(diff / 86400)} d ago`;
    return formatDate(iso);
  }

  function pct(score) {
    const n = Number(score);
    if (score == null || Number.isNaN(n)) return '—';
    return (n * 100).toFixed(1) + '%';
  }

  // Risk badge — always icon/text, never color alone
  function riskBadge(level) {
    const map = {
      low:      { cls: 'badge-success', label: 'Low risk' },
      medium:   { cls: 'badge-warning', label: 'Medium risk' },
      high:     { cls: 'badge-error',   label: 'High risk' },
      critical: { cls: 'badge-error',   label: 'Critical' },
    };
    const m = map[String(level || '').toLowerCase()];
    if (!m) return '<span class="badge badge-neutral">Unknown</span>';
    return `<span class="badge ${m.cls}"><span class="badge-dot" aria-hidden="true"></span>${m.label}</span>`;
  }

  // ── Dialogs (focus-trapped, Escape-safe, focus-restoring) ────
  // Returns { close }. onConfirm may be async: the dialog shows a
  // loading state and stays open (with the error) if it throws.
  function dialog({ title, description, bodyHTML = '', confirmLabel = 'Confirm', cancelLabel = 'Cancel', danger = false, onConfirm }) {
    const opener = document.activeElement;
    const overlay = el(
      `<div class="modal-overlay">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="dlg-title">
          <h2 class="modal-title" id="dlg-title">${esc(title)}</h2>
          ${description ? `<p class="dialog-desc">${esc(description)}</p>` : ''}
          ${bodyHTML}
          <p class="dialog-error" role="alert" hidden></p>
          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" data-dialog-cancel>${esc(cancelLabel)}</button>
            <button type="button" class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-dialog-confirm>${esc(confirmLabel)}</button>
          </div>
        </div>
      </div>`
    );
    const modal = overlay.querySelector('.modal');
    const confirmBtn = overlay.querySelector('[data-dialog-confirm]');
    const cancelBtn = overlay.querySelector('[data-dialog-cancel]');
    const errorEl = overlay.querySelector('.dialog-error');

    function close() {
      document.removeEventListener('keydown', onKeydown, true);
      overlay.remove();
      if (opener && document.contains(opener)) opener.focus();
    }
    function onKeydown(e) {
      if (e.key === 'Escape') { e.stopPropagation(); close(); return; }
      if (e.key !== 'Tab') return;
      const items = [...modal.querySelectorAll('button, [href], input, select, textarea')]
        .filter(n => !n.disabled && n.offsetParent !== null);
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }

    cancelBtn.addEventListener('click', close);
    overlay.addEventListener('mousedown', (e) => { if (e.target === overlay) close(); });
    document.addEventListener('keydown', onKeydown, true);
    confirmBtn.addEventListener('click', async () => {
      errorEl.hidden = true;
      const done = UI.showLoading(confirmBtn, 'Working…');
      try {
        if (onConfirm) await onConfirm(overlay);
        done();
        close();
      } catch (err) {
        done();
        errorEl.textContent = err?.message || 'Something went wrong. Please try again.';
        errorEl.hidden = false;
      }
    });

    document.body.appendChild(overlay);
    (modal.querySelector('input, select, textarea') || confirmBtn).focus();
    return { close };
  }

  function initials(name) {
    if (!name) return '?';
    return String(name).trim().split(/\s+/).map(w => w[0]).join('').toUpperCase().slice(0, 2);
  }

  return { esc, el, toast, showLoading, dialog, formatDate, formatTime, formatRelative, pct, riskBadge, initials };
})();
