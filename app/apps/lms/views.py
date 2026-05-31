from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.lms.models import (
    Enrollment,
    Lesson,
    LessonProgress,
    Role,
)


def _user_has_access(user, lesson: Lesson) -> bool:
    """Сотрудник имеет доступ к уроку если урок принадлежит курсу его роли."""
    profile = getattr(user, 'profile', None)
    if not profile:
        return False
    role_ids = list(profile.roles.values_list('id', flat=True))
    return lesson.topic.course.course_roles.filter(role_id__in=role_ids).exists()


def _get_or_create_enrollment(user, course) -> Enrollment:
    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    if enrollment:
        return enrollment
    # На всякий случай: если сигнал не сработал, создаём при первом заходе
    profile = getattr(user, 'profile', None)
    role = None
    if profile:
        role = (
            course.course_roles
            .filter(role__in=profile.roles.all())
            .select_related('role')
            .first()
        )
    return Enrollment.objects.create(
        user=user,
        course=course,
        assigned_role=role.role if role else Role.objects.first(),
    )


@login_required
def lesson_view(request, pk: int):
    lesson = get_object_or_404(
        Lesson.objects.select_related('topic__course')
        .prefetch_related('blocks', 'questions__answers'),
        pk=pk,
    )

    if not lesson.is_published:
        return render(request, 'lesson_unavailable.html', {'lesson': lesson}, status=403)

    if not _user_has_access(request.user, lesson):
        return render(request, 'lesson_unavailable.html', {'lesson': lesson}, status=403)

    enrollment = _get_or_create_enrollment(request.user, lesson.topic.course)
    progress = LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).first()

    # Соседние уроки внутри темы
    siblings = list(lesson.topic.lessons.filter(is_published=True).order_by('order', 'id'))
    prev_lesson = next_lesson = None
    for i, l in enumerate(siblings):
        if l.id == lesson.id:
            if i > 0:
                prev_lesson = siblings[i - 1]
            if i + 1 < len(siblings):
                next_lesson = siblings[i + 1]
            break

    context = {
        'lesson': lesson,
        'course': lesson.topic.course,
        'topic': lesson.topic,
        'enrollment': enrollment,
        'is_completed': bool(progress and progress.is_completed),
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    }
    if lesson.kind == Lesson.Kind.CONTENT:
        context['blocks'] = lesson.blocks.order_by('order', 'id')
    else:
        context['questions'] = lesson.questions.order_by('order', 'id').prefetch_related('answers')
    return render(request, 'lesson.html', context)


@login_required
@require_POST
def lesson_complete_view(request, pk: int):
    """Сотрудник нажал «Завершить» (для CONTENT-уроков)."""
    lesson = get_object_or_404(Lesson, pk=pk, is_published=True)
    if not _user_has_access(request.user, lesson):
        return JsonResponse({'ok': False, 'message': 'Доступ запрещён'}, status=403)

    enrollment = _get_or_create_enrollment(request.user, lesson.topic.course)
    progress, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment, lesson=lesson,
        defaults={'is_completed': True, 'completed_at': timezone.now()},
    )
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()

    return JsonResponse({'ok': True, 'message': 'Урок завершён'})


@login_required
@require_POST
def lesson_quiz_submit_view(request, pk: int):
    """Проверяет ответы на тест и при 100% правильных — отмечает урок завершённым."""
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related('questions__answers'),
        pk=pk, kind=Lesson.Kind.QUIZ, is_published=True,
    )
    if not _user_has_access(request.user, lesson):
        return JsonResponse({'ok': False, 'message': 'Доступ запрещён'}, status=403)

    total = 0
    correct = 0
    details = []
    questions = lesson.questions.order_by('order', 'id').prefetch_related('answers')

    for q in questions:
        total += 1
        correct_ids = {str(a.id) for a in q.answers.all() if a.is_correct}
        selected_ids = set(request.POST.getlist(f'q_{q.id}'))
        is_right = bool(correct_ids) and selected_ids == correct_ids
        if is_right:
            correct += 1
        details.append({
            'question_id': q.id,
            'is_right': is_right,
            'correct_answer_ids': list(correct_ids),
        })

    enrollment = _get_or_create_enrollment(request.user, lesson.topic.course)
    score_pct = int(correct / total * 100) if total else 0
    passed = score_pct == 100

    # Фиксируем КАЖДУЮ попытку (в т.ч. неуспешную) и её результат.
    progress, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment, lesson=lesson,
    )
    progress.attempts += 1
    progress.score_pct = score_pct
    # Урок остаётся пройденным даже после повторной попытки с ошибками —
    # доступ к пройденному тесту сохраняется.
    if passed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
    progress.save()

    return JsonResponse({
        'ok': True,
        'total': total,
        'correct': correct,
        'score_pct': score_pct,
        'passed': passed,
        'attempts': progress.attempts,
        'details': details,
    })
