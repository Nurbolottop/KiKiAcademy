/* ===================================================
   KIKI Academy — Login Page Script
   =================================================== */

(function () {
  'use strict';

  /* ─── Theme ─────────────────────────────────────── */
  const html        = document.documentElement;
  const themeToggle = document.getElementById('theme-toggle');

  const STORAGE_KEY = 'kiki-theme';
  const DARK        = 'dark';
  const LIGHT       = 'light';

  function getPreferredTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === DARK || saved === LIGHT) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? DARK : LIGHT;
  }

  function applyTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    themeToggle.setAttribute(
      'aria-label',
      theme === DARK ? 'Переключить на светлую тему' : 'Переключить на тёмную тему'
    );
  }

  function toggleTheme() {
    const current = html.getAttribute('data-theme') === DARK ? DARK : LIGHT;
    applyTheme(current === DARK ? LIGHT : DARK);
  }

  // Init
  applyTheme(getPreferredTheme());
  themeToggle.addEventListener('click', toggleTheme);

  // Sync across tabs
  window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY && e.newValue) applyTheme(e.newValue);
  });


  /* ─── Phone Mask ─────────────────────────────────── */
  const phoneInput = document.getElementById('phone');

  function formatPhone(value) {
    const hasPlus = value.startsWith('+');
    let digits = value.replace(/\D/g, '');
    if (!digits) return hasPlus ? '+' : '';

    let result = hasPlus ? '+' : '';

    if (digits.startsWith('7') || digits.startsWith('8')) {
      // RU/KZ format: X (XXX) XXX-XX-XX
      digits = digits.slice(0, 11);
      result += digits.charAt(0);
      if (digits.length > 1) result += ' (' + digits.slice(1, 4);
      if (digits.length > 4) result += ') ' + digits.slice(4, 7);
      if (digits.length > 7) result += '-' + digits.slice(7, 9);
      if (digits.length > 9) result += '-' + digits.slice(9, 11);
      return result;
    } 
    else if (digits.startsWith('996')) {
      // KR format: 996 (XXX) XX-XX-XX
      digits = digits.slice(0, 12);
      result += '996';
      if (digits.length > 3) result += ' (' + digits.slice(3, 6);
      if (digits.length > 6) result += ') ' + digits.slice(6, 8);
      if (digits.length > 8) result += '-' + digits.slice(8, 10);
      if (digits.length > 10) result += '-' + digits.slice(10, 12);
      return result;
    }
    else if (digits.startsWith('0')) {
      // KR local format: 0XXX XX-XX-XX
      digits = digits.slice(0, 10);
      result += digits.slice(0, 4);
      if (digits.length > 4) result += ' ' + digits.slice(4, 6);
      if (digits.length > 6) result += '-' + digits.slice(6, 8);
      if (digits.length > 8) result += '-' + digits.slice(8, 10);
      return result;
    }
    else {
      // Free format fallback
      result += digits;
      return result;
    }
  }

  phoneInput.addEventListener('input', function () {
    const pos   = this.selectionStart;
    const old   = this.value;
    this.value  = formatPhone(this.value);

    // Restore cursor roughly
    const diff = this.value.length - old.length;
    try { this.setSelectionRange(pos + diff, pos + diff); } catch (_) {}
    clearFieldError('field-phone');
  });

  // Listeners removed for free input


  /* ─── Password Toggle ────────────────────────────── */
  const passwordInput = document.getElementById('password');
  const toggleBtn     = document.getElementById('toggle-password');
  const eyeShow       = toggleBtn.querySelector('.eye-icon--show');
  const eyeHide       = toggleBtn.querySelector('.eye-icon--hide');

  toggleBtn.addEventListener('click', function () {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    eyeShow.style.display = isPassword ? 'none'  : '';
    eyeHide.style.display = isPassword ? ''      : 'none';
    toggleBtn.setAttribute('aria-label', isPassword ? 'Скрыть пароль' : 'Показать пароль');
    passwordInput.focus();
  });

  passwordInput.addEventListener('input', () => clearFieldError('field-password'));


  /* ─── Validation ─────────────────────────────────── */
  function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const error = field.querySelector('.field__error');
    field.classList.add('has-error');
    error.textContent = message;
  }

  function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const error = field.querySelector('.field__error');
    field.classList.remove('has-error');
    error.textContent = '';
  }

  function validatePhone(value) {
    const digits = value.replace(/\D/g, '');
    return digits.length >= 10 && digits.length <= 15;
  }

  function validatePassword(value) {
    return value.trim().length >= 1;
  }


  /* ─── Form Submit ────────────────────────────────── */
  const form      = document.getElementById('login-form');
  const submitBtn = document.getElementById('submit-btn');

  form.addEventListener('submit', function (e) {
    let valid = true;

    // Phone
    if (!validatePhone(phoneInput.value)) {
      showFieldError('field-phone', 'Введите корректный номер телефона');
      valid = false;
    } else {
      clearFieldError('field-phone');
    }

    // Password
    if (!validatePassword(passwordInput.value)) {
      showFieldError('field-password', 'Введите пароль');
      valid = false;
    } else {
      clearFieldError('field-password');
    }

    if (!valid) return;

    setLoading(true);
  });

  function setLoading(state) {
    submitBtn.disabled = state;
    submitBtn.classList.toggle('loading', state);
  }


  /* ─── Input live clear on typing ─────────────────── */
  [phoneInput, passwordInput].forEach((input) => {
    input.addEventListener('input', () => {
      const fieldId = input.closest('.field').id;
      if (fieldId) clearFieldError(fieldId);
    });
  });

})();
