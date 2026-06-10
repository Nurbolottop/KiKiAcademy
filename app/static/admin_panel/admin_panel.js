// ─── THEME (применяется до отрисовки, чтобы не было вспышки) ─
(function () {
  const saved = localStorage.getItem('kiki-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

(function () {
  'use strict';

  // ─── THEME TOGGLE ──────────────────────────────────────────
  function getTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  }
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kiki-theme', theme);
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      btn.dataset.themeCurrent = theme;
    });
  }
  function setupThemeToggle() {
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      btn.dataset.themeCurrent = getTheme();
      btn.addEventListener('click', () => {
        setTheme(getTheme() === 'dark' ? 'light' : 'dark');
      });
    });
  }

  // ─── LANGUAGE SWITCH ───────────────────────────────────────
  const LANG_CODES = ['ru', 'ky'];
  function changeLanguage(code) {
    if (!LANG_CODES.includes(code)) return;
    // Срезаем текущий префикс языка из URL, чтобы set_language редиректнул правильно
    const re = new RegExp('^/(' + LANG_CODES.join('|') + ')(/|$)');
    const pathWithoutLang = window.location.pathname.replace(re, '/');
    const next = pathWithoutLang + window.location.search;

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
  }
  function setupLanguageSwitch() {
    document.querySelectorAll('[data-lang-switch]').forEach((sel) => {
      sel.addEventListener('change', () => changeLanguage(sel.value));
    });
  }

  // ─── CSRF ──────────────────────────────────────────────────
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }
  function getCsrf() {
    const input = document.querySelector('input[name=csrfmiddlewaretoken]');
    return (input && input.value) || getCookie('csrftoken') || '';
  }

  // ─── TOAST ─────────────────────────────────────────────────
  function ensureToastContainer() {
    let el = document.getElementById('toast-container');
    if (!el) {
      el = document.createElement('div');
      el.id = 'toast-container';
      el.className = 'toast-container';
      document.body.appendChild(el);
    }
    return el;
  }

  function showToast(message, type = 'info', timeout = 3500) {
    const container = ensureToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `
      <span class="toast__icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ⓘ'}</span>
      <span class="toast__msg"></span>
      <button class="toast__close" aria-label="Закрыть">×</button>
    `;
    toast.querySelector('.toast__msg').textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast--show'));

    const close = () => {
      toast.classList.remove('toast--show');
      setTimeout(() => toast.remove(), 250);
    };
    toast.querySelector('.toast__close').addEventListener('click', close);
    if (timeout) setTimeout(close, timeout);
  }

  // ─── CONFIRM MODAL ─────────────────────────────────────────
  function showConfirm({ title, text, confirmText = 'Подтвердить', confirmType = 'danger' }) {
    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.className = 'modal';
      modal.innerHTML = `
        <div class="modal__backdrop"></div>
        <div class="modal__dialog">
          <h3 class="modal__title"></h3>
          <p class="modal__text"></p>
          <div class="modal__actions">
            <button type="button" class="btn btn--ghost" data-action="cancel">Отмена</button>
            <button type="button" class="btn btn--${confirmType}" data-action="confirm"></button>
          </div>
        </div>
      `;
      modal.querySelector('.modal__title').textContent = title || 'Подтвердите действие';
      modal.querySelector('.modal__text').textContent = text || '';
      modal.querySelector('[data-action="confirm"]').textContent = confirmText;

      document.body.appendChild(modal);
      requestAnimationFrame(() => modal.classList.add('modal--show'));

      const close = (value) => {
        modal.classList.remove('modal--show');
        setTimeout(() => modal.remove(), 200);
        resolve(value);
      };
      modal.addEventListener('click', (e) => {
        if (e.target.matches('.modal__backdrop, [data-action="cancel"]')) close(false);
        if (e.target.matches('[data-action="confirm"]')) close(true);
      });
      document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { document.removeEventListener('keydown', esc); close(false); }
      });
    });
  }

  // ─── BUTTON LOADING ────────────────────────────────────────
  function setLoading(btn, isLoading) {
    if (!btn) return;
    if (isLoading) {
      btn.dataset.originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Подождите...';
    } else {
      btn.disabled = false;
      if (btn.dataset.originalText) btn.innerHTML = btn.dataset.originalText;
    }
  }

  // ─── AJAX FORM SUBMIT ──────────────────────────────────────
  async function ajaxSubmit(form) {
    const submitBtn = form.querySelector('[type=submit]');
    setLoading(submitBtn, true);

    try {
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        },
      });

      let data = {};
      try { data = await response.json(); } catch (_) { /* not JSON */ }

      if (response.ok && data.ok) {
        showToast(data.message || 'Готово', 'success');
        if (data.redirect_url) {
          setTimeout(() => { window.location.href = data.redirect_url; }, 400);
        } else if (form.dataset.reloadOnSuccess !== 'false') {
          setTimeout(() => window.location.reload(), 400);
        }
      } else {
        showToast(data.message || 'Ошибка', 'error');
        setLoading(submitBtn, false);
      }
    } catch (err) {
      showToast('Ошибка сети', 'error');
      setLoading(submitBtn, false);
    }
  }

  function setupAjaxForms(root = document) {
    root.querySelectorAll('form[data-ajax]').forEach((form) => {
      if (form.dataset.ajaxBound) return;
      form.dataset.ajaxBound = '1';

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const confirmText = form.dataset.confirm;
        if (confirmText) {
          const ok = await showConfirm({
            title: form.dataset.confirmTitle || 'Подтвердите действие',
            text: confirmText,
            confirmText: form.dataset.confirmButton || 'Подтвердить',
            confirmType: form.dataset.confirmType || 'danger',
          });
          if (!ok) return;
        }
        ajaxSubmit(form);
      });
    });
  }

  // ─── LIVE SEARCH (DEBOUNCE) ─────────────────────────────────
  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  function setupLiveSearch() {
    const form = document.querySelector('form.filters');
    if (!form) return;

    const target = document.querySelector('[data-table-target]');
    if (!target) return;

    const onChange = debounce(async () => {
      const params = new URLSearchParams(new FormData(form));
      try {
        const res = await fetch(`${form.action || window.location.pathname}?${params}`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const html = await res.text();
        target.innerHTML = html;
        setupAjaxForms(target);
        setupBulk();
        setupRowLinks(target);
        const newUrl = `${window.location.pathname}?${params}`;
        window.history.replaceState({}, '', newUrl);
      } catch (err) {
        showToast('Ошибка поиска', 'error');
      }
    }, 300);

    form.querySelectorAll('input, select').forEach((el) => {
      const evt = el.tagName === 'SELECT' ? 'change' : 'input';
      el.addEventListener(evt, onChange);
    });

    form.addEventListener('submit', (e) => e.preventDefault());
  }

  // ─── BULK SELECT ───────────────────────────────────────────
  function setupBulk() {
    const checkAll = document.querySelector('[data-check-all]');
    const checks = document.querySelectorAll('[data-bulk-check]');
    const toolbar = document.querySelector('[data-bulk-toolbar]');
    const counter = document.querySelector('[data-bulk-counter]');

    if (!checks.length || !toolbar) return;

    function refresh() {
      const selected = Array.from(checks).filter((c) => c.checked);
      const count = selected.length;
      if (counter) counter.textContent = count;
      toolbar.classList.toggle('is-active', count > 0);
      if (checkAll) {
        checkAll.checked = count === checks.length && count > 0;
        checkAll.indeterminate = count > 0 && count < checks.length;
      }
    }

    if (checkAll) {
      checkAll.addEventListener('change', () => {
        checks.forEach((c) => { c.checked = checkAll.checked; });
        refresh();
      });
    }
    checks.forEach((c) => c.addEventListener('change', refresh));

    toolbar.querySelectorAll('[data-bulk-action]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const action = btn.dataset.bulkAction;
        const selected = Array.from(checks).filter((c) => c.checked).map((c) => c.value);
        if (!selected.length) return;

        const ok = await showConfirm({
          title: 'Массовое действие',
          text: `Применить «${btn.textContent.trim()}» к ${selected.length} сотруднику(ам)?`,
          confirmText: btn.textContent.trim(),
          confirmType: btn.dataset.confirmType || 'warning',
        });
        if (!ok) return;

        setLoading(btn, true);
        const fd = new FormData();
        fd.append('action', action);
        selected.forEach((id) => fd.append('ids', id));

        try {
          const res = await fetch(toolbar.dataset.bulkUrl, {
            method: 'POST',
            body: fd,
            headers: {
              'X-Requested-With': 'XMLHttpRequest',
              'X-CSRFToken': getCsrf(),
            },
          });
          const data = await res.json();
          if (data.ok) {
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 500);
          } else {
            showToast(data.message || 'Ошибка', 'error');
            setLoading(btn, false);
          }
        } catch (e) {
          showToast('Ошибка сети', 'error');
          setLoading(btn, false);
        }
      });
    });

    refresh();
  }

  // ─── FILE UPLOAD ZONES ─────────────────────────────────────
  function setupFileUploads(root = document) {
    root.querySelectorAll('[data-upload-zone]').forEach((zone) => {
      if (zone.dataset.uploadBound) return;
      zone.dataset.uploadBound = '1';

      const input = zone.querySelector('[data-upload-input]');
      const preview = zone.querySelector('.upload-zone__preview');
      const clearBtn = zone.querySelector('[data-upload-clear]');
      if (!input || !preview) return;

      function setPreviewFromFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          preview.src = e.target.result;
          zone.classList.add('upload-zone--has-file');
          removeClearMarker();
        };
        reader.readAsDataURL(file);
      }

      function clearMarkerName() {
        return input.name + '-clear';
      }
      function ensureClearMarker() {
        let marker = zone.querySelector(`input[name="${clearMarkerName()}"]`);
        if (!marker) {
          marker = document.createElement('input');
          marker.type = 'hidden';
          marker.name = clearMarkerName();
          marker.value = '1';
          zone.appendChild(marker);
        }
      }
      function removeClearMarker() {
        const marker = zone.querySelector(`input[name="${clearMarkerName()}"]`);
        if (marker) marker.remove();
      }

      zone.addEventListener('click', (e) => {
        if (e.target.closest('[data-upload-clear]')) return;
        input.click();
      });

      ['dragenter', 'dragover'].forEach((evt) => {
        zone.addEventListener(evt, (e) => {
          e.preventDefault();
          e.stopPropagation();
          zone.classList.add('upload-zone--dragging');
        });
      });
      ['dragleave', 'drop'].forEach((evt) => {
        zone.addEventListener(evt, (e) => {
          e.preventDefault();
          e.stopPropagation();
          zone.classList.remove('upload-zone--dragging');
        });
      });

      zone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files && e.dataTransfer.files[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
          showToast('Можно загружать только изображения', 'error');
          return;
        }
        input.files = e.dataTransfer.files;
        setPreviewFromFile(file);
      });

      input.addEventListener('change', () => {
        const file = input.files && input.files[0];
        if (file) setPreviewFromFile(file);
      });

      if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          input.value = '';
          preview.src = '';
          zone.classList.remove('upload-zone--has-file');
          ensureClearMarker();
        });
      }
    });
  }

  // ─── ROLE CHIPS ────────────────────────────────────────────
  function setupRoleChips(root = document) {
    root.querySelectorAll('[data-role-chips]').forEach((container) => {
      if (container.dataset.chipsBound) return;
      container.dataset.chipsBound = '1';

      const url = container.dataset.toggleUrl;
      container.querySelectorAll('.chip').forEach((chip) => {
        chip.addEventListener('click', async () => {
          if (chip.disabled) return;
          const roleId = chip.dataset.roleId;
          const roleTitle = chip.dataset.roleTitle || 'роль';

          chip.classList.add('chip--loading');
          chip.disabled = true;

          try {
            const fd = new FormData();
            fd.append('role_id', roleId);
            const res = await fetch(url, {
              method: 'POST',
              body: fd,
              headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrf(),
              },
            });
            const data = await res.json();
            if (data.ok) {
              if (data.active) chip.classList.add('chip--active');
              else chip.classList.remove('chip--active');
              showToast(data.message, 'success', 2000);
            } else {
              showToast(data.message || 'Ошибка', 'error');
            }
          } catch (err) {
            showToast(`Не удалось обновить роль «${roleTitle}»`, 'error');
          } finally {
            chip.classList.remove('chip--loading');
            chip.disabled = false;
          }
        });
      });
    });
  }

  // ─── DRAG & DROP REORDER ───────────────────────────────────
  function setupReorderLists(root = document) {
    root.querySelectorAll('[data-reorder-list]').forEach((list) => {
      if (list.dataset.dndBound) return;
      list.dataset.dndBound = '1';

      let dragged = null;
      const url = list.dataset.reorderUrl;

      list.querySelectorAll('[data-id]').forEach((item) => {
        const handle = item.querySelector('[data-drag-handle]');
        if (!handle) return;
        item.draggable = false;

        handle.addEventListener('mousedown', () => { item.draggable = true; });
        handle.addEventListener('mouseup', () => { item.draggable = false; });

        item.addEventListener('dragstart', (e) => {
          dragged = item;
          item.classList.add('is-dragging');
          e.dataTransfer.effectAllowed = 'move';
        });
        item.addEventListener('dragend', () => {
          item.classList.remove('is-dragging');
          item.draggable = false;
          dragged = null;
          saveOrder();
        });
        item.addEventListener('dragover', (e) => {
          e.preventDefault();
          if (!dragged || dragged === item) return;
          const rect = item.getBoundingClientRect();
          const after = (e.clientY - rect.top) / rect.height > 0.5;
          if (after) item.parentNode.insertBefore(dragged, item.nextSibling);
          else item.parentNode.insertBefore(dragged, item);
        });
      });

      async function saveOrder() {
        const ids = Array.from(list.querySelectorAll('[data-id]')).map((el) => el.dataset.id);
        try {
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'X-CSRFToken': getCsrf(),
            },
            body: JSON.stringify({ ids }),
          });
          const data = await res.json();
          if (!data.ok) showToast(data.message || 'Ошибка', 'error');
        } catch (e) { showToast('Ошибка сохранения порядка', 'error'); }
      }
    });
  }

  // ─── INLINE FORM TOGGLE ────────────────────────────────────
  function setupInlineFormToggle(root = document) {
    root.querySelectorAll('[data-show-form]').forEach((btn) => {
      if (btn.dataset.toggleBound) return;
      btn.dataset.toggleBound = '1';
      btn.addEventListener('click', () => {
        const target = document.getElementById(btn.dataset.showForm);
        if (target) {
          target.hidden = false;
          const firstInput = target.querySelector('input, select, textarea');
          if (firstInput) firstInput.focus();
        }
      });
    });
    root.querySelectorAll('[data-hide-form]').forEach((btn) => {
      if (btn.dataset.hideBound) return;
      btn.dataset.hideBound = '1';
      btn.addEventListener('click', () => {
        const target = document.getElementById(btn.dataset.hideForm);
        if (target) {
          target.hidden = true;
          target.reset();
        }
      });
    });
  }

  // ─── ANSWER TOGGLE (правильный/неправильный) ───────────────
  function setupAnswerToggle(root = document) {
    root.querySelectorAll('[data-answer-toggle]').forEach((btn) => {
      if (btn.dataset.toggleBound) return;
      btn.dataset.toggleBound = '1';
      btn.addEventListener('click', async () => {
        const url = btn.dataset.answerToggle;
        btn.disabled = true;
        try {
          const res = await fetch(url, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() },
          });
          const data = await res.json();
          if (data.ok) {
            const row = btn.closest('.answer-row');
            if (data.is_correct) {
              row.classList.add('answer-row--correct');
              btn.textContent = '✓';
            } else {
              row.classList.remove('answer-row--correct');
              btn.textContent = '○';
            }
          } else {
            showToast(data.message || 'Ошибка', 'error');
          }
        } catch (e) {
          showToast('Ошибка сети', 'error');
        } finally {
          btn.disabled = false;
        }
      });
    });
  }

  // ─── ROW LINKS ─────────────────────────────────────────────
  function setupRowLinks(root = document) {
    // tr[data-href] — строки таблиц; [data-href] с data-id — карточки (курсы и т.п.)
    root.querySelectorAll('tr[data-href], [data-href][data-id]').forEach((row) => {
      if (row.dataset.rowBound) return;
      row.dataset.rowBound = '1';
      row.style.cursor = 'pointer';
      row.addEventListener('click', (e) => {
        if (e.target.closest('[data-no-link], [data-drag-handle], input, label, a, button')) return;
        const url = row.dataset.href;
        if (e.metaKey || e.ctrlKey || e.button === 1) {
          window.open(url, '_blank');
        } else {
          window.location.href = url;
        }
      });
    });
  }

  // ─── INIT ──────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    setupThemeToggle();
    setupLanguageSwitch();
    setupAjaxForms();
    setupLiveSearch();
    setupBulk();
    setupRowLinks();
    setupRoleChips();
    setupFileUploads();
    setupReorderLists();
    setupInlineFormToggle();
    setupAnswerToggle();
  });
})();
