// Страница урока: завершение + викторина
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

  // ─── Отметка «Пройдено» ─────────────────────────────────────
  function setupComplete() {
    const form = document.querySelector('[data-lesson-complete]');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type=submit]');
      btn.disabled = true;
      btn.textContent = '…';
      try {
        const res = await fetch(form.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() },
        });
        const data = await res.json();
        if (data.ok) {
          form.outerHTML = `<div class="lesson-status lesson-status--done">✓ ${data.message}</div>`;
          setTimeout(() => window.location.reload(), 700);
        } else {
          btn.disabled = false;
          btn.textContent = '⚠ ' + (data.message || 'Ошибка');
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = '⚠ Ошибка сети';
      }
    });
  }

  // ─── Викторина ──────────────────────────────────────────────
  function setupQuiz() {
    const form = document.getElementById('quiz-form');
    const result = document.getElementById('quiz-result');
    if (!form || !result) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type=submit]');
      btn.disabled = true;
      btn.textContent = '…';

      try {
        const fd = new FormData(form);
        const res = await fetch(form.action, {
          method: 'POST',
          body: fd,
          headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() },
        });
        const data = await res.json();
        if (!data.ok) {
          btn.disabled = false;
          btn.textContent = '⚠';
          return;
        }

        // Подсветка вопросов и ответов
        form.querySelectorAll('.quiz-question').forEach((q) => {
          q.classList.remove('is-right', 'is-wrong');
        });
        form.querySelectorAll('.quiz-answer').forEach((a) => {
          a.classList.remove('is-correct', 'is-wrong');
        });

        (data.details || []).forEach((d) => {
          const q = form.querySelector(`[data-question-id="${d.question_id}"]`);
          if (!q) return;
          q.classList.add(d.is_right ? 'is-right' : 'is-wrong');
          d.correct_answer_ids.forEach((aid) => {
            const inp = q.querySelector(`input[value="${aid}"]`);
            if (inp) inp.closest('.quiz-answer').classList.add('is-correct');
          });
        });

        // Результат
        result.hidden = false;
        result.className = 'quiz-result quiz-result--' + (data.passed ? 'passed' : 'failed');
        result.innerHTML = `
          <div class="quiz-result__score">${data.score_pct}%</div>
          <div class="quiz-result__text">
            ${data.correct} / ${data.total} ${(window._i18n && window._i18n.correctAnswers) || 'правильных ответов'}
            ${data.passed
              ? '<br><strong style="color:var(--green-text)">' + ((window._i18n && window._i18n.passed) || 'Тест пройден') + ' ✓</strong>'
              : '<br><strong style="color:#ef4444">' + ((window._i18n && window._i18n.tryAgain) || 'Попробуйте ещё раз') + '</strong>'}
          </div>
        `;
        result.scrollIntoView({ behavior: 'smooth', block: 'center' });

        if (data.passed) {
          btn.disabled = true;
          btn.textContent = '✓';
        } else {
          btn.disabled = false;
          btn.textContent = (window._i18n && window._i18n.checkAgain) || 'Проверить';
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = '⚠';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupComplete();
    setupQuiz();
  });
})();
