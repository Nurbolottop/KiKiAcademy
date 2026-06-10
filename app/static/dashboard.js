// ─── Тема: синхронизировано с admin (тот же localStorage) ─
(function () {
  const saved = localStorage.getItem('kiki-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

(function () {
  'use strict';

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }
  function getCsrf() {
    const input = document.querySelector('input[name=csrfmiddlewaretoken]');
    return (input && input.value) || getCookie('csrftoken') || '';
  }
  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;'
    }[c]));
  }
  function debounce(fn, ms) {
    let t;
    return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  }

  // ─── Theme toggle ──────────────────────────────────────────
  function setupTheme() {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('kiki-theme', next);
    });
  }

  // ─── Language switch ───────────────────────────────────────
  const LANG_CODES = ['ru', 'ky'];
  function setupLangSwitch() {
    document.querySelectorAll('[data-lang-switch]').forEach((sel) => {
      sel.addEventListener('change', () => {
        const code = sel.value;
        if (!LANG_CODES.includes(code)) return;
        const re = new RegExp('^/(' + LANG_CODES.join('|') + ')(/|$)');
        const next = window.location.pathname.replace(re, '/') + window.location.search;
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/i18n/setlang/';
        form.style.display = 'none';
        form.innerHTML = `
          <input name="csrfmiddlewaretoken" value="${getCsrf()}">
          <input name="language" value="${code}">
          <input name="next" value="${next}">
        `;
        document.body.appendChild(form);
        form.submit();
      });
    });
  }

  // ─── Progress bar animation ────────────────────────────────
  function setupProgressBar() {
    document.querySelectorAll('.progress-fill[data-target]').forEach((bar) => {
      const target = parseInt(bar.dataset.target, 10) || 0;
      requestAnimationFrame(() => {
        bar.style.transition = 'width .8s ease';
        bar.style.width = target + '%';
      });
    });
  }

  // ─── Accordion ─────────────────────────────────────────────
  function setupAccordion() {
    document.querySelectorAll('.acc-item').forEach((item) => {
      const header = item.querySelector('.acc-header');
      if (!header) return;
      header.addEventListener('click', () => {
        if (header.disabled) return;
        const expanded = header.getAttribute('aria-expanded') === 'true';
        header.setAttribute('aria-expanded', String(!expanded));
        item.classList.toggle('is-open', !expanded);
      });
    });

    // Авто-открыть якорный курс из URL hash (#topic-N)
    const hash = window.location.hash;
    if (hash && hash.startsWith('#topic-')) {
      const target = document.querySelector(hash);
      if (target) {
        const item = target.closest('.acc-item');
        if (item) {
          const header = item.querySelector('.acc-header');
          if (header && !header.disabled) {
            header.setAttribute('aria-expanded', 'true');
            item.classList.add('is-open');
            setTimeout(() => target.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
          }
        }
      }
    }
  }

  // ─── Этапы: сворачивание/разворачивание ───────────────────
  function setupTopicAccordion() {
    document.querySelectorAll('[data-topic-toggle]').forEach((header) => {
      header.addEventListener('click', (e) => {
        // Клик по кнопке/ссылке (Продолжить/Повторить) — не сворачивать
        if (e.target.closest('a, button')) return;
        const block = header.closest('.topic-block');
        if (block) block.classList.toggle('is-open');
      });
    });
  }

  // ─── Search (AJAX) ─────────────────────────────────────────
  function setupSearch() {
    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    const clearBtn = document.getElementById('search-clear');
    const focusBtn = document.getElementById('btn-search-focus');
    if (!input || !results) return;

    function hide() {
      results.hidden = true;
      results.innerHTML = '';
    }
    function render(items) {
      if (!items.length) {
        results.innerHTML = `<div class="search-results__empty">${window._i18n.nothingFound}</div>`;
      } else {
        results.innerHTML = items.map((r) => `
          <div class="search-results__item">
            <span class="search-results__icon">${r.icon}</span>
            <div class="search-results__body">
              <div class="search-results__title">${escapeHtml(r.title)}</div>
              <div class="search-results__meta">${escapeHtml(r.course)}${r.topic ? ' · ' + escapeHtml(r.topic) : ''}</div>
            </div>
            <span class="search-results__type">${r.type === 'topic' ? window._i18n.topic : window._i18n.lesson}</span>
          </div>
        `).join('');
      }
      results.hidden = false;
    }

    const onInput = debounce(async () => {
      const q = input.value.trim();
      clearBtn.style.display = q ? '' : 'none';
      if (q.length < 2) { hide(); return; }
      try {
        const url = input.dataset.searchUrl + '?q=' + encodeURIComponent(q);
        const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const data = await res.json();
        if (data.ok) render(data.results);
      } catch (e) { /* network */ }
    }, 250);

    input.addEventListener('input', onInput);
    input.addEventListener('focus', () => {
      if (input.value.trim().length >= 2) onInput();
    });
    document.addEventListener('click', (e) => {
      if (!results.contains(e.target) && e.target !== input) hide();
    });
    clearBtn.addEventListener('click', () => {
      input.value = '';
      clearBtn.style.display = 'none';
      hide();
      input.focus();
    });
    if (focusBtn) {
      focusBtn.addEventListener('click', () => {
        input.focus();
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    }
  }

  // ─── i18n из data-атрибутов (для динамических строк) ───────
  function loadI18n() {
    const root = document.documentElement;
    const lang = root.getAttribute('lang') || 'ru';
    const strings = {
      ru: { nothingFound: 'Ничего не найдено', topic: 'тема', lesson: 'урок' },
      ky: { nothingFound: 'Эч нерсе табылган жок', topic: 'тема', lesson: 'сабак' },
    };
    window._i18n = strings[lang] || strings.ru;
  }

  // ─── Init ──────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    loadI18n();
    setupTheme();
    setupLangSwitch();
    setupProgressBar();
    setupAccordion();
    setupTopicAccordion();
    setupSearch();
  });
})();
