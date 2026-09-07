/**
 * NEURO_PREDICT_SYS — UI Utilities
 *
 * Pure presentation helpers. No auth, no API, no state.
 */
const UI = (() => {
  // ── Toast notification ───────────────────────────────────────
  function toast(message, type = 'info') {
    const styles = {
      info:    'border-[#00ffcc] text-[#00ffcc]',
      success: 'border-green-500 text-green-400',
      error:   'border-[#ff2d78] text-[#ff2d78]',
      warning: 'border-[#ffe04a] text-[#ffe04a]',
    };
    const icons = { info: 'info', success: 'check_circle', error: 'error', warning: 'warning' };
    const el = document.createElement('div');
    el.className = `fixed top-20 right-4 z-[100] px-4 py-3 bg-[#141422] border ${styles[type]} rounded-lg backdrop-blur-xl shadow-lg flex items-center gap-3 transform translate-x-full transition-transform duration-300`;
    el.innerHTML = `
      <span class="material-symbols-outlined text-lg">${icons[type]}</span>
      <span style="font-family:'Space Grotesk',monospace;font-size:12px">${message}</span>
    `;
    document.body.appendChild(el);
    requestAnimationFrame(() => el.classList.remove('translate-x-full'));
    setTimeout(() => {
      el.classList.add('translate-x-full');
      setTimeout(() => el.remove(), 300);
    }, 3000);
  }

  // ── Loading spinner ──────────────────────────────────────────
  function showLoading(element) {
    const original = element.innerHTML;
    element.dataset.originalContent = original;
    element.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span>';
    element.disabled = true;
    return () => { element.innerHTML = element.dataset.originalContent; element.disabled = false; };
  }

  // ── Date formatting ──────────────────────────────────────────
  function formatDate(iso) {
    if (!iso) return 'N/A';
    return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  // ── Confidence as percentage ─────────────────────────────────
  function pct(score) {
    return (score * 100).toFixed(1) + '%';
  }

  // ── Risk level color classes ─────────────────────────────────
  function riskColor(level) {
    const m = {
      low: 'text-green-400 bg-green-400/10 border-green-400/30',
      medium: 'text-[#ffe04a] bg-[#ffe04a]/10 border-[#ffe04a]/30',
      high: 'text-[#ff2d78] bg-[#ff2d78]/10 border-[#ff2d78]/30',
      critical: 'text-red-500 bg-red-500/10 border-red-500/30',
    };
    return m[level] || m.low;
  }

  // ── Initials helper ──────────────────────────────────────────
  function initials(name) {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  }

  return { toast, showLoading, formatDate, pct, riskColor, initials };
})();
