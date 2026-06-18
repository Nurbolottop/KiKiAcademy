from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import founder_required
from apps.admin_panel.forms import (
    AnswerForm,
    BlockImageForm,
    BlockTextForm,
    BlockVideoForm,
    CourseForm,
    EmployeeCreateForm,
    EmployeeEditForm,
    LessonForm,
    PasswordResetForm,
    QuestionForm,
    SiteSettingsForm,
    TopicForm,
)
from apps.admin_panel.utils import ajax_error, ajax_ok, is_ajax
from apps.base.models import Settings
from apps.lms.models import (
    Answer,
    Course,
    Enrollment,
    Lesson,
    LessonBlock,
    LessonProgress,
    Question,
    Role,
    Topic,
    UserProfile,
)


# ─── DASHBOARD ─────────────────────────────────────────────────────

@founder_required
def dashboard_view(request):
    context = {
        'employees_count': UserProfile.objects.filter(status=UserProfile.Status.ACTIVE).count(),
        'employees_blocked': UserProfile.objects.filter(status=UserProfile.Status.BLOCKED).count(),
        'employees_fired': UserProfile.objects.filter(status=UserProfile.Status.FIRED).count(),
        'courses_total': Course.objects.count(),
        'topics_total': Topic.objects.count(),
        'enrollments_active': Enrollment.objects.filter(completed_at__isnull=True).count(),
        'enrollments_completed': Enrollment.objects.filter(completed_at__isnull=False).count(),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── EMPLOYEES ─────────────────────────────────────────────────────

def _is_founder_profile(profile: UserProfile) -> bool:
    return profile.roles.filter(code=Role.Code.FOUNDER).exists()


def _filtered_employees_qs(request):
    qs = (
        UserProfile.objects
        .select_related('user')
        .prefetch_related('roles')
        .exclude(roles__code=Role.Code.FOUNDER)
        .order_by('-hired_at')
        .distinct()
    )

    search = (request.GET.get('q') or '').strip()
    status = request.GET.get('status') or ''
    role_id = request.GET.get('role') or ''

    if search:
        qs = qs.filter(
            Q(user__phone__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )
    if status in UserProfile.Status.values:
        qs = qs.filter(status=status)
    if role_id:
        qs = qs.filter(roles__id=role_id)
    return qs, search, status, role_id


@founder_required
def employees_list_view(request):
    qs, search, status, role_id = _filtered_employees_qs(request)
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page': page,
        'search': search,
        'status': status,
        'role_id': role_id,
        'statuses': UserProfile.Status.choices,
        'roles': Role.objects.exclude(code=Role.Code.FOUNDER).order_by('title'),
    }

    if is_ajax(request):
        return render(request, 'admin_panel/employees/_table.html', context)
    return render(request, 'admin_panel/employees/list.html', context)


@founder_required
def employee_create_view(request):
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(request, f'Сотрудник {profile.user} создан')
            return redirect('admin_panel:employee_detail', pk=profile.pk)
    else:
        form = EmployeeCreateForm()
    return render(request, 'admin_panel/employees/form.html', {'form': form, 'mode': 'create'})


@founder_required
def employee_detail_view(request, pk: int):
    profile = get_object_or_404(
        UserProfile.objects.select_related('user').prefetch_related('roles'),
        pk=pk,
    )
    enrollments = (
        Enrollment.objects
        .filter(user=profile.user)
        .select_related('course', 'assigned_role')
        .order_by('-started_at')
    )
    available_roles = Role.objects.exclude(code=Role.Code.FOUNDER).order_by('title')
    active_role_ids = set(profile.roles.values_list('id', flat=True))

    # Результаты тестов сотрудника (по урокам типа QUIZ, которые он проходил)
    quiz_progress = (
        LessonProgress.objects
        .filter(enrollment__user=profile.user, lesson__kind=Lesson.Kind.QUIZ, attempts__gt=0)
        .select_related('lesson', 'lesson__topic', 'lesson__topic__course')
        .order_by('lesson__topic__course__order', 'lesson__topic__order', 'lesson__order')
    )
    quiz_results = []
    for p in quiz_progress:
        total = p.lesson.questions.count()
        quiz_results.append({
            'course': p.lesson.topic.course.title,
            'topic': p.lesson.topic.title,
            'lesson': p.lesson.title,
            'score_pct': p.score_pct,
            'threshold': p.lesson.pass_threshold,
            'attempts': p.attempts,
            'passed': p.score_pct >= p.lesson.pass_threshold,
            'correct': round(p.score_pct * total / 100) if total else 0,
            'total': total,
            'updated_at': p.updated_at,
        })

    context = {
        'profile': profile,
        'enrollments': enrollments,
        'quiz_results': quiz_results,
        'is_founder': _is_founder_profile(profile),
        'available_roles': available_roles,
        'active_role_ids': active_role_ids,
    }
    return render(request, 'admin_panel/employees/detail.html', context)


@founder_required
@require_POST
def employee_roles_toggle_view(request, pk: int):
    profile = get_object_or_404(UserProfile.objects.select_related('user'), pk=pk)
    if _is_founder_profile(profile):
        msg = 'Нельзя редактировать роли администратора'
        if is_ajax(request):
            return ajax_error(msg)
        messages.error(request, msg)
        return redirect('admin_panel:employee_detail', pk=pk)

    role_id = request.POST.get('role_id')
    if not role_id:
        return ajax_error('Не указана роль') if is_ajax(request) else redirect('admin_panel:employee_detail', pk=pk)

    role = get_object_or_404(Role.objects.exclude(code=Role.Code.FOUNDER), pk=role_id)

    if profile.roles.filter(pk=role.pk).exists():
        profile.roles.remove(role)
        active = False
        msg = f'Роль «{role.title}» удалена'
    else:
        profile.roles.add(role)
        active = True
        msg = f'Роль «{role.title}» добавлена'

    if is_ajax(request):
        return ajax_ok(msg, role_id=role.pk, active=active)
    messages.success(request, msg)
    return redirect('admin_panel:employee_detail', pk=pk)


@founder_required
def employee_edit_view(request, pk: int):
    profile = get_object_or_404(UserProfile.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения сохранены')
            return redirect('admin_panel:employee_detail', pk=profile.pk)
    else:
        form = EmployeeEditForm(instance=profile)
    return render(request, 'admin_panel/employees/form.html', {
        'form': form,
        'mode': 'edit',
        'profile': profile,
    })


def _apply_status_action(request, profile: UserProfile, action: str):
    if action == 'block':
        if _is_founder_profile(profile):
            return False, 'Нельзя заблокировать администратора'
        profile.status = UserProfile.Status.BLOCKED
        profile.save()
        return True, 'Сотрудник заблокирован'

    if action == 'activate':
        profile.status = UserProfile.Status.ACTIVE
        profile.fired_at = None
        profile.save()
        return True, 'Сотрудник активирован'

    if action == 'fire':
        if _is_founder_profile(profile):
            return False, 'Нельзя уволить администратора'
        profile.status = UserProfile.Status.FIRED
        profile.fired_at = timezone.now()
        profile.save()
        return True, 'Сотрудник уволен'

    return False, 'Неизвестное действие'


def _status_action_view(request, pk: int, action: str):
    profile = get_object_or_404(UserProfile, pk=pk)
    ok, msg = _apply_status_action(request, profile, action)

    if is_ajax(request):
        if ok:
            return ajax_ok(msg, status_value=profile.status, status_label=profile.get_status_display())
        return ajax_error(msg)

    (messages.success if ok else messages.error)(request, msg)
    return redirect('admin_panel:employee_detail', pk=pk)


@founder_required
@require_POST
def employee_block_view(request, pk: int):
    return _status_action_view(request, pk, 'block')


@founder_required
@require_POST
def employee_activate_view(request, pk: int):
    return _status_action_view(request, pk, 'activate')


@founder_required
@require_POST
def employee_fire_view(request, pk: int):
    return _status_action_view(request, pk, 'fire')


@founder_required
def employee_reset_password_view(request, pk: int):
    profile = get_object_or_404(UserProfile.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            profile.user.set_password(form.cleaned_data['password'])
            profile.user.save()
            if is_ajax(request):
                return ajax_ok('Пароль обновлён')
            messages.success(request, 'Пароль обновлён')
            return redirect('admin_panel:employee_detail', pk=pk)
        if is_ajax(request):
            return ajax_error(next(iter(form.errors.values()))[0])
    else:
        form = PasswordResetForm()
    return render(request, 'admin_panel/employees/reset_password.html', {
        'form': form,
        'profile': profile,
    })


@founder_required
@require_POST
def employee_delete_view(request, pk: int):
    profile = get_object_or_404(UserProfile.objects.select_related('user'), pk=pk)
    if _is_founder_profile(profile):
        msg = 'Нельзя удалить администратора'
        if is_ajax(request):
            return ajax_error(msg)
        messages.error(request, msg)
        return redirect('admin_panel:employee_detail', pk=pk)

    user_str = str(profile.user)
    profile.user.delete()

    if is_ajax(request):
        return ajax_ok(f'Сотрудник {user_str} удалён', redirect_url='/staff/employees/')
    messages.success(request, f'Сотрудник {user_str} удалён')
    return redirect('admin_panel:employees')


@founder_required
@require_POST
def employees_bulk_action_view(request):
    action = request.POST.get('action', '')
    ids = request.POST.getlist('ids')

    if action not in {'block', 'activate', 'fire'}:
        return ajax_error('Неизвестное действие') if is_ajax(request) else redirect('admin_panel:employees')
    if not ids:
        return ajax_error('Не выбраны сотрудники') if is_ajax(request) else redirect('admin_panel:employees')

    profiles = UserProfile.objects.filter(pk__in=ids).select_related('user')
    affected = 0
    skipped_founders = 0
    for profile in profiles:
        if _is_founder_profile(profile):
            skipped_founders += 1
            continue
        _apply_status_action(request, profile, action)
        affected += 1

    msg_parts = [f'Обработано: {affected}']
    if skipped_founders:
        msg_parts.append(f'пропущено администраторов: {skipped_founders}')
    msg = ', '.join(msg_parts)

    if is_ajax(request):
        return ajax_ok(msg)
    messages.success(request, msg)
    return redirect('admin_panel:employees')


# ─── COURSES ────────────────────────────────────────────────────────

def _next_order(qs) -> int:
    last = qs.order_by('-order').values_list('order', flat=True).first()
    return (last or 0) + 1


@founder_required
def courses_view(request):
    courses = (
        Course.objects
        .prefetch_related('topics', 'course_roles__role')
        .order_by('order', 'id')
    )
    return render(request, 'admin_panel/courses/list.html', {'courses': courses})


@founder_required
def course_create_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            if not course.order:
                course.order = _next_order(Course.objects)
            course.save()
            form._sync_roles(course)
            messages.success(request, f'Курс «{course.title}» создан')
            return redirect('admin_panel:course_detail', pk=course.pk)
    else:
        form = CourseForm(initial={'order': _next_order(Course.objects)})
    return render(request, 'admin_panel/courses/form.html', {'form': form, 'mode': 'create'})


@founder_required
def course_detail_view(request, pk: int):
    course = get_object_or_404(
        Course.objects.prefetch_related('topics__lessons', 'topics__roles', 'course_roles__role'),
        pk=pk,
    )
    return render(request, 'admin_panel/courses/detail.html', {
        'course': course,
        'topic_form': TopicForm(),
    })


@founder_required
def course_edit_view(request, pk: int):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            form._sync_roles(course)
            messages.success(request, 'Курс обновлён')
            return redirect('admin_panel:course_detail', pk=course.pk)
    else:
        form = CourseForm(instance=course)
    return render(request, 'admin_panel/courses/form.html', {
        'form': form,
        'mode': 'edit',
        'course': course,
    })


@founder_required
@require_POST
def course_delete_view(request, pk: int):
    course = get_object_or_404(Course, pk=pk)
    title = course.title
    course.delete()
    msg = f'Курс «{title}» удалён'
    if is_ajax(request):
        return ajax_ok(msg, redirect_url='/staff/courses/')
    messages.success(request, msg)
    return redirect('admin_panel:courses')


@founder_required
@require_POST
def courses_reorder_view(request):
    """Принимает {ids: [course_id, ...]} в новом порядке."""
    import json
    try:
        data = json.loads(request.body or '{}')
        ids = data.get('ids', [])
    except Exception:
        return ajax_error('Некорректные данные')

    for index, course_id in enumerate(ids, start=1):
        Course.objects.filter(pk=course_id).update(order=index)
    return ajax_ok('Порядок обновлён')


# ─── TOPICS ─────────────────────────────────────────────────────────

@founder_required
@require_POST
def topic_create_view(request, course_pk: int):
    course = get_object_or_404(Course, pk=course_pk)
    form = TopicForm(request.POST)
    if form.is_valid():
        topic = form.save(commit=False)
        topic.course = course
        topic.order = _next_order(course.topics)
        topic.save()
        if is_ajax(request):
            return ajax_ok('Тема создана', topic_id=topic.id, topic_title=topic.title)
        messages.success(request, f'Тема «{topic.title}» создана')
        return redirect('admin_panel:topic_detail', course_pk=course.pk, pk=topic.pk)
    if is_ajax(request):
        return ajax_error(next(iter(form.errors.values()))[0])
    messages.error(request, 'Ошибка создания темы')
    return redirect('admin_panel:course_detail', pk=course.pk)


@founder_required
def topic_detail_view(request, course_pk: int, pk: int):
    topic = get_object_or_404(
        Topic.objects.select_related('course').prefetch_related('lessons', 'roles'),
        pk=pk, course_id=course_pk,
    )
    # Роли курса — из них выбираем, кому видна тема. Пусто = всем ролям курса.
    course_roles = [cr.role for cr in topic.course.course_roles.select_related('role')]
    topic_role_ids = set(topic.roles.values_list('id', flat=True))
    return render(request, 'admin_panel/courses/topic_detail.html', {
        'course': topic.course,
        'topic': topic,
        'lesson_form': LessonForm(),
        'course_roles': course_roles,
        'topic_role_ids': topic_role_ids,
    })


@founder_required
@require_POST
def topic_roles_update_view(request, course_pk: int, pk: int):
    """Обновляет роли, которым видна тема (ограничено ролями курса)."""
    topic = get_object_or_404(Topic, pk=pk, course_id=course_pk)
    course_role_ids = set(topic.course.course_roles.values_list('role_id', flat=True))
    selected = {int(x) for x in request.POST.getlist('roles') if x.isdigit()} & course_role_ids
    topic.roles.set(Role.objects.filter(id__in=selected))
    msg = 'Доступ темы обновлён'
    if is_ajax(request):
        return ajax_ok(msg)
    messages.success(request, msg)
    return redirect('admin_panel:topic_detail', course_pk=course_pk, pk=pk)


@founder_required
@require_POST
def topic_edit_view(request, course_pk: int, pk: int):
    topic = get_object_or_404(Topic, pk=pk, course_id=course_pk)
    title = (request.POST.get('title') or '').strip()
    if not title:
        return ajax_error('Название обязательно') if is_ajax(request) else redirect('admin_panel:course_detail', pk=course_pk)
    topic.title = title
    topic.save()
    if is_ajax(request):
        return ajax_ok('Тема обновлена', title=topic.title)
    return redirect('admin_panel:topic_detail', course_pk=course_pk, pk=pk)


@founder_required
@require_POST
def topic_delete_view(request, course_pk: int, pk: int):
    topic = get_object_or_404(Topic, pk=pk, course_id=course_pk)
    topic.delete()
    if is_ajax(request):
        return ajax_ok('Тема удалена')
    messages.success(request, 'Тема удалена')
    return redirect('admin_panel:course_detail', pk=course_pk)


@founder_required
@require_POST
def topics_reorder_view(request, course_pk: int):
    import json
    try:
        ids = json.loads(request.body or '{}').get('ids', [])
    except Exception:
        return ajax_error('Некорректные данные')
    for index, topic_id in enumerate(ids, start=1):
        Topic.objects.filter(pk=topic_id, course_id=course_pk).update(order=index)
    return ajax_ok('Порядок обновлён')


# ─── LESSONS ────────────────────────────────────────────────────────

@founder_required
@require_POST
def lesson_create_view(request, course_pk: int, topic_pk: int):
    topic = get_object_or_404(Topic, pk=topic_pk, course_id=course_pk)
    form = LessonForm(request.POST)
    if form.is_valid():
        lesson = form.save(commit=False)
        lesson.topic = topic
        lesson.order = _next_order(topic.lessons)
        lesson.save()
        if is_ajax(request):
            return ajax_ok('Урок создан', redirect_url=f'/staff/courses/{course_pk}/topics/{topic_pk}/lessons/{lesson.pk}/')
        return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson.pk)
    if is_ajax(request):
        return ajax_error(next(iter(form.errors.values()))[0])
    return redirect('admin_panel:topic_detail', course_pk=course_pk, pk=topic_pk)


def _get_lesson_or_404(course_pk: int, topic_pk: int, pk: int) -> Lesson:
    return get_object_or_404(
        Lesson.objects.select_related('topic__course'),
        pk=pk, topic_id=topic_pk, topic__course_id=course_pk,
    )


@founder_required
def lesson_edit_view(request, course_pk: int, topic_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, pk)
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Урок сохранён')
            return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=pk)
    else:
        form = LessonForm(instance=lesson)

    context = {
        'form': form,
        'lesson': lesson,
        'course': lesson.topic.course,
        'topic': lesson.topic,
    }
    if lesson.kind == Lesson.Kind.QUIZ:
        context['questions'] = (
            lesson.questions.prefetch_related('answers').order_by('order', 'id')
        )
    else:
        context['blocks'] = lesson.blocks.order_by('order', 'id')
    return render(request, 'admin_panel/courses/lesson_form.html', context)


@founder_required
@require_POST
def lesson_delete_view(request, course_pk: int, topic_pk: int, pk: int):
    lesson = get_object_or_404(Lesson, pk=pk, topic_id=topic_pk, topic__course_id=course_pk)
    lesson.delete()
    if is_ajax(request):
        return ajax_ok('Урок удалён')
    messages.success(request, 'Урок удалён')
    return redirect('admin_panel:topic_detail', course_pk=course_pk, pk=topic_pk)


@founder_required
@require_POST
def lessons_reorder_view(request, course_pk: int, topic_pk: int):
    import json
    try:
        ids = json.loads(request.body or '{}').get('ids', [])
    except Exception:
        return ajax_error('Некорректные данные')
    for index, lesson_id in enumerate(ids, start=1):
        Lesson.objects.filter(
            pk=lesson_id, topic_id=topic_pk, topic__course_id=course_pk,
        ).update(order=index)
    return ajax_ok('Порядок обновлён')


# ─── LESSON BLOCKS (CONTENT) ───────────────────────────────────────

_BLOCK_FORMS = {
    LessonBlock.Kind.TEXT: BlockTextForm,
    LessonBlock.Kind.IMAGE: BlockImageForm,
    LessonBlock.Kind.VIDEO: BlockVideoForm,
}


@founder_required
def block_create_view(request, course_pk: int, topic_pk: int, lesson_pk: int, kind: str):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    kind = kind.upper()
    if kind not in _BLOCK_FORMS:
        messages.error(request, 'Неизвестный тип блока')
        return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)
    FormCls = _BLOCK_FORMS[kind]

    if request.method == 'POST':
        form = FormCls(request.POST, request.FILES)
        if form.is_valid():
            block = form.save(commit=False)
            block.lesson = lesson
            block.kind = kind
            block.order = _next_order(lesson.blocks)
            block.save()
            messages.success(request, 'Блок создан')
            return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)
    else:
        form = FormCls()

    return render(request, 'admin_panel/courses/block_form.html', {
        'form': form,
        'kind': kind,
        'lesson': lesson,
        'course': lesson.topic.course,
        'topic': lesson.topic,
        'mode': 'create',
    })


@founder_required
def block_edit_view(request, course_pk: int, topic_pk: int, lesson_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    block = get_object_or_404(LessonBlock, pk=pk, lesson=lesson)
    FormCls = _BLOCK_FORMS.get(block.kind, BlockTextForm)

    if request.method == 'POST':
        form = FormCls(request.POST, request.FILES, instance=block)
        if form.is_valid():
            form.save()
            messages.success(request, 'Блок обновлён')
            return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)
    else:
        form = FormCls(instance=block)

    return render(request, 'admin_panel/courses/block_form.html', {
        'form': form,
        'kind': block.kind,
        'block': block,
        'lesson': lesson,
        'course': lesson.topic.course,
        'topic': lesson.topic,
        'mode': 'edit',
    })


@founder_required
@require_POST
def block_delete_view(request, course_pk: int, topic_pk: int, lesson_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    LessonBlock.objects.filter(pk=pk, lesson=lesson).delete()
    if is_ajax(request):
        return ajax_ok('Блок удалён')
    messages.success(request, 'Блок удалён')
    return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)


@founder_required
@require_POST
def blocks_reorder_view(request, course_pk: int, topic_pk: int, lesson_pk: int):
    import json
    try:
        ids = json.loads(request.body or '{}').get('ids', [])
    except Exception:
        return ajax_error('Некорректные данные')
    for index, block_id in enumerate(ids, start=1):
        LessonBlock.objects.filter(
            pk=block_id, lesson_id=lesson_pk, lesson__topic_id=topic_pk,
            lesson__topic__course_id=course_pk,
        ).update(order=index)
    return ajax_ok('Порядок обновлён')


# ─── QUIZ: QUESTIONS & ANSWERS ─────────────────────────────────────

@founder_required
@require_POST
def question_create_view(request, course_pk: int, topic_pk: int, lesson_pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    form = QuestionForm(request.POST)
    if form.is_valid():
        question = form.save(commit=False)
        question.lesson = lesson
        question.order = _next_order(lesson.questions)
        question.save()
        if is_ajax(request):
            return ajax_ok('Вопрос создан', question_id=question.id)
        return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)
    if is_ajax(request):
        return ajax_error(next(iter(form.errors.values()))[0])
    return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)


@founder_required
@require_POST
def question_edit_view(request, course_pk: int, topic_pk: int, lesson_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    question = get_object_or_404(Question, pk=pk, lesson=lesson)
    text = (request.POST.get('text') or '').strip()
    if not text:
        return ajax_error('Текст вопроса обязателен') if is_ajax(request) else redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)
    question.text = text
    question.save()
    if is_ajax(request):
        return ajax_ok('Вопрос обновлён')
    return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)


@founder_required
@require_POST
def question_delete_view(request, course_pk: int, topic_pk: int, lesson_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    Question.objects.filter(pk=pk, lesson=lesson).delete()
    if is_ajax(request):
        return ajax_ok('Вопрос удалён')
    messages.success(request, 'Вопрос удалён')
    return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)


@founder_required
@require_POST
def questions_reorder_view(request, course_pk: int, topic_pk: int, lesson_pk: int):
    import json
    try:
        ids = json.loads(request.body or '{}').get('ids', [])
    except Exception:
        return ajax_error('Некорректные данные')
    for index, q_id in enumerate(ids, start=1):
        Question.objects.filter(
            pk=q_id, lesson_id=lesson_pk, lesson__topic_id=topic_pk,
            lesson__topic__course_id=course_pk,
        ).update(order=index)
    return ajax_ok('Порядок обновлён')


@founder_required
@require_POST
def answer_create_view(request, course_pk: int, topic_pk: int, lesson_pk: int, question_pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    question = get_object_or_404(Question, pk=question_pk, lesson=lesson)
    form = AnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(commit=False)
        answer.question = question
        answer.order = _next_order(question.answers)
        answer.save()
        if is_ajax(request):
            return ajax_ok('Ответ добавлен', answer_id=answer.id, is_correct=answer.is_correct)
        return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)
    if is_ajax(request):
        return ajax_error(next(iter(form.errors.values()))[0])
    return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)


@founder_required
@require_POST
def answer_toggle_view(request, course_pk: int, topic_pk: int, lesson_pk: int, question_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    answer = get_object_or_404(Answer, pk=pk, question_id=question_pk, question__lesson=lesson)
    answer.is_correct = not answer.is_correct
    answer.save()
    return ajax_ok('Сохранено', is_correct=answer.is_correct)


@founder_required
@require_POST
def answer_delete_view(request, course_pk: int, topic_pk: int, lesson_pk: int, question_pk: int, pk: int):
    lesson = _get_lesson_or_404(course_pk, topic_pk, lesson_pk)
    Answer.objects.filter(pk=pk, question_id=question_pk, question__lesson=lesson).delete()
    if is_ajax(request):
        return ajax_ok('Ответ удалён')
    return redirect('admin_panel:lesson_edit', course_pk=course_pk, topic_pk=topic_pk, pk=lesson_pk)


# ─── PLACEHOLDERS ──────────────────────────────────────────────────

@founder_required
def programs_view(request):
    return render(request, 'admin_panel/placeholder.html', {'section': 'Программы обучения'})


@founder_required
def settings_view(request):
    instance = Settings.get_singleton()

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки сайта сохранены')
            return redirect('admin_panel:settings')
        messages.error(request, 'Проверьте поля формы')
    else:
        form = SiteSettingsForm(instance=instance)

    return render(request, 'admin_panel/settings/edit.html', {
        'form': form,
        'instance': instance,
    })
