from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.permissions import is_founder, post_login_redirect_url
from apps.accounts.utils import normalize_phone
from apps.lms.models import Course, Lesson, Topic
from apps.lms.services import build_user_progress, find_next_lesson, overall_progress


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(post_login_redirect_url(request.user))

    error = None
    if request.method == 'POST':
        phone = normalize_phone(request.POST.get('phone', ''))
        password = request.POST.get('password', '')

        user = authenticate(request, username=phone, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or post_login_redirect_url(user))
        error = 'Неверный номер телефона или пароль'

    return render(request, 'login.html', {'error': error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    if is_founder(request.user):
        return redirect('admin_panel:dashboard')

    profile = getattr(request.user, 'profile', None)
    roles = list(profile.roles.all()) if profile else []
    full_access = bool(profile and profile.full_access)

    if full_access:
        courses = Course.objects.all().order_by('order', 'id')
    else:
        role_ids = [r.id for r in roles]
        courses = (
            Course.objects
            .filter(course_roles__role_id__in=role_ids)
            .distinct()
            .order_by('order', 'id')
        )

    course_statuses = build_user_progress(request.user, courses, full_access=full_access)
    done, in_progress, locked, total = overall_progress(course_statuses)
    overall_percent = int(done / total * 100) if total else 0
    next_lesson = find_next_lesson(course_statuses)

    context = {
        'profile': profile,
        'roles': roles,
        'course_statuses': course_statuses,
        'overall_percent': overall_percent,
        'done_topics': done,
        'in_progress_topics': in_progress,
        'locked_topics': locked,
        'total_topics': total,
        'next_lesson': next_lesson,
    }
    return render(request, 'dashboard.html', context)


@login_required
def search_view(request):
    """AJAX-поиск по темам и урокам в рамках курсов пользователя."""
    query = (request.GET.get('q') or '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'ok': True, 'results': []})

    profile = getattr(request.user, 'profile', None)
    if not profile:
        return JsonResponse({'ok': True, 'results': []})

    role_ids = list(profile.roles.values_list('id', flat=True))
    accessible_course_ids = list(
        Course.objects
        .filter(course_roles__role_id__in=role_ids)
        .values_list('id', flat=True)
        .distinct()
    )

    topics = (
        Topic.objects
        .filter(course_id__in=accessible_course_ids, title__icontains=query)
        .select_related('course')[:10]
    )
    lessons = (
        Lesson.objects
        .filter(
            topic__course_id__in=accessible_course_ids,
            is_published=True,
            title__icontains=query,
        )
        .select_related('topic__course')[:10]
    )

    results = []
    for t in topics:
        results.append({
            'type': 'topic',
            'title': t.title,
            'course': t.course.title,
            'icon': '📂',
        })
    for l in lessons:
        results.append({
            'type': 'lesson',
            'title': l.title,
            'course': l.topic.course.title,
            'topic': l.topic.title,
            'icon': '❓' if l.kind == 'QUIZ' else '📄',
        })
    return JsonResponse({'ok': True, 'results': results})
