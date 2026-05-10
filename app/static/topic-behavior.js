/* ===================================================
   KIKI Academy — Topic: Behaviour JS
   =================================================== */

(function () {
  'use strict';

  /* ── Theme ──────────────────────────────────────── */
  const html        = document.documentElement;
  const themeToggle = document.getElementById('theme-toggle');
  const STORAGE_KEY = 'kiki-theme';

  function applyTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  applyTheme(localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : 'dark');

  themeToggle.addEventListener('click', () => {
    applyTheme(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  });

  window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY && e.newValue) applyTheme(e.newValue);
  });


  /* ── Scroll Reveal ──────────────────────────────── */
  const revealEls = document.querySelectorAll('.reveal');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => entry.target.classList.add('visible'), i * 70);
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  revealEls.forEach(el => obs.observe(el));


  /* ── Video play ─────────────────────────────────── */
  const overlay = document.getElementById('video-overlay');
  const iframe  = document.getElementById('video-iframe');
  const btnPlay = document.getElementById('btn-play');

  function playVideo() {
    if (!overlay || !iframe) return;
    iframe.src = 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1&rel=0';
    iframe.style.display = 'block';
    overlay.style.display = 'none';
  }

  overlay?.addEventListener('click', playVideo);
  btnPlay?.addEventListener('click', (e) => { e.stopPropagation(); playVideo(); });


  /* ── Action buttons ─────────────────────────────── */
  document.getElementById('btn-finish')?.addEventListener('click', () => {
    const btn = document.getElementById('btn-finish');
    btn.textContent = '✓ Завершено!';
    btn.style.background = 'linear-gradient(135deg, #22C55E, #16A34A)';
    btn.disabled = true;
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 1200);
  });

  document.getElementById('btn-repeat')?.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    // Re-trigger reveal animations
    document.querySelectorAll('.reveal').forEach(el => el.classList.remove('visible'));
    setTimeout(() => {
      revealEls.forEach(el => obs.observe(el));
    }, 100);
  });

  document.getElementById('btn-back')?.addEventListener('click', (e) => {
    e.preventDefault();
    history.length > 1 ? history.back() : (window.location.href = 'dashboard.html');
  });

})();
