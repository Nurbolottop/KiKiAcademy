/* ===================================================
   KIKI Academy — Dashboard JS (redesign)
   =================================================== */

(function () {
  'use strict';

  /* ─── Theme ──────────────────────────────────────── */
  const html        = document.documentElement;
  const themeToggle = document.getElementById('theme-toggle');
  const STORAGE_KEY = 'kiki-theme';

  function applyTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  function getPreferredTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'dark' || saved === 'light') return saved;
    return 'dark';
  }

  applyTheme(getPreferredTheme());
  themeToggle.addEventListener('click', () => {
    applyTheme(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  });
  window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY && e.newValue) applyTheme(e.newValue);
  });


  /* ─── Progress Bar ───────────────────────────────── */
  const fill = document.querySelector('.progress-fill');
  if (fill) {
    setTimeout(() => { fill.style.width = (fill.dataset.target || '0') + '%'; }, 300);
  }


  /* ─── Accordion ──────────────────────────────────── */
  const accItems = document.querySelectorAll('.acc-item');

  accItems.forEach(item => {
    const header = item.querySelector('.acc-header');
    header.addEventListener('click', () => {
      const isOpen = item.classList.contains('is-open');

      // Close all
      accItems.forEach(i => {
        i.classList.remove('is-open');
        i.querySelector('.acc-header').setAttribute('aria-expanded', 'false');
      });

      // Open clicked (toggle)
      if (!isOpen) {
        item.classList.add('is-open');
        header.setAttribute('aria-expanded', 'true');
      }
    });
  });


  /* ─── Search ─────────────────────────────────────── */
  const searchInput = document.getElementById('search-input');
  const searchClear = document.getElementById('search-clear');
  const noResults   = document.getElementById('no-results');

  // All theme cards with searchable name
  const allThemeCards = document.querySelectorAll('.theme-card');

  function filterThemes(query) {
    const q = query.trim().toLowerCase();
    let visibleCount = 0;

    accItems.forEach(item => {
      const cards  = item.querySelectorAll('.theme-card');
      let catVisible = 0;

      cards.forEach(card => {
        const name = (card.dataset.name || '').toLowerCase();
        const desc = (card.querySelector('.theme-card__desc')?.textContent || '').toLowerCase();
        const match = !q || name.includes(q) || desc.includes(q);
        card.style.display = match ? '' : 'none';
        if (match) catVisible++;
      });

      // Show/hide entire category based on matches
      item.style.display = catVisible > 0 ? '' : 'none';

      // If searching and category has results — open it
      if (q && catVisible > 0) {
        item.classList.add('is-open');
        item.querySelector('.acc-header').setAttribute('aria-expanded', 'true');
      } else if (q && catVisible === 0) {
        item.classList.remove('is-open');
      }

      visibleCount += catVisible;
    });

    if (noResults) noResults.style.display = visibleCount === 0 ? 'block' : 'none';
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const val = searchInput.value;
      if (searchClear) searchClear.style.display = val ? 'flex' : 'none';
      filterThemes(val);
    });
  }

  if (searchClear) {
    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      searchClear.style.display = 'none';
      filterThemes('');
      // Reset all open state
      accItems.forEach(i => {
        i.classList.remove('is-open');
        i.querySelector('.acc-header').setAttribute('aria-expanded', 'false');
        i.style.display = '';
        i.querySelectorAll('.theme-card').forEach(c => c.style.display = '');
      });
      searchInput.focus();
    });
  }


  /* ─── "Продолжить обучение" ──────────────────────── */
  document.getElementById('btn-continue')?.addEventListener('click', () => {
    // Find first current theme card and scroll to it
    const current = document.querySelector('.theme-card--current');
    if (!current) return;

    // Open its parent accordion
    const parentItem = current.closest('.acc-item');
    if (parentItem && !parentItem.classList.contains('is-open')) {
      accItems.forEach(i => {
        i.classList.remove('is-open');
        i.querySelector('.acc-header').setAttribute('aria-expanded', 'false');
      });
      parentItem.classList.add('is-open');
      parentItem.querySelector('.acc-header').setAttribute('aria-expanded', 'true');
    }

    setTimeout(() => {
      current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      current.style.outline = '2px solid var(--brand)';
      setTimeout(() => { current.style.outline = ''; }, 1800);
    }, 380);
  });


  /* ─── "Найти тему" — фокус на поиск ─────────────── */
  document.getElementById('btn-search-focus')?.addEventListener('click', () => {
    if (!searchInput) return;
    searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => searchInput.focus(), 300);
  });


  /* ─── Theme action buttons ───────────────────────── */
  document.querySelectorAll('.theme-btn-action:not(.theme-btn-action--locked)').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const card  = btn.closest('.theme-card');
      const title = card?.querySelector('.theme-card__title')?.textContent || 'тему';
      // Navigate to category page as placeholder
      window.location.href = 'category.html';
    });
  });

})();
