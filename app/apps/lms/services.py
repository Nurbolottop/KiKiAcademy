from dataclasses import dataclass
from typing import Iterable

from django.db.models import Prefetch

from apps.lms.models import Course, Enrollment, Lesson, LessonProgress, Topic


@dataclass
class LessonStatus:
    lesson: Lesson
    state: str  # 'done' | 'current' | 'locked'

    @property
    def is_completed(self) -> bool:
        return self.state == 'done'

    @property
    def accessible(self) -> bool:
        """Пройденный урок и текущий доступны для открытия; будущие — нет."""
        return self.state in ('done', 'current')


@dataclass
class TopicStatus:
    topic: Topic
    state: str  # 'done' | 'current' | 'locked'
    completed_lessons: int
    total_lessons: int
    lessons: list[LessonStatus]

    @property
    def percent(self) -> int:
        if self.total_lessons == 0:
            return 100 if self.state == 'done' else 0
        return int(self.completed_lessons / self.total_lessons * 100)

    @property
    def entry_lesson(self) -> Lesson | None:
        """Урок, на который ведёт кнопка темы: первый незавершённый, иначе первый."""
        for ls in self.lessons:
            if ls.state == 'current':
                return ls.lesson
        return self.lessons[0].lesson if self.lessons else None


@dataclass
class CourseStatus:
    course: Course
    enrollment: Enrollment | None
    state: str  # 'done' | 'current' | 'locked'
    topics: list[TopicStatus]
    completed_topics: int
    total_topics: int

    @property
    def percent(self) -> int:
        if self.total_topics == 0:
            return 100 if self.state == 'done' else 0
        return int(self.completed_topics / self.total_topics * 100)


def _topic_status(topic: Topic, completed_lesson_ids: set[int]) -> TopicStatus:
    published_lessons = [l for l in topic.lessons.all() if l.is_published]
    total = len(published_lessons)
    completed = sum(1 for l in published_lessons if l.id in completed_lesson_ids)

    # Статусы уроков: пройденные — done, первый непройденный — current,
    # последующие непройденные — locked. Пройденные остаются доступными.
    lesson_statuses: list[LessonStatus] = []
    seen_current = False
    for l in published_lessons:
        if l.id in completed_lesson_ids:
            lesson_statuses.append(LessonStatus(lesson=l, state='done'))
        elif not seen_current:
            lesson_statuses.append(LessonStatus(lesson=l, state='current'))
            seen_current = True
        else:
            lesson_statuses.append(LessonStatus(lesson=l, state='locked'))

    if total == 0 or completed == total:
        state = 'done'
    else:
        state = 'current'  # будет сдвинуто на locked если предыдущая тема не done

    return TopicStatus(
        topic=topic, state=state,
        completed_lessons=completed, total_lessons=total,
        lessons=lesson_statuses,
    )


def _lock_topic_lessons(ts: TopicStatus) -> None:
    """Заблокировать ещё не пройденные уроки темы (пройденные оставить доступными)."""
    for ls in ts.lessons:
        if ls.state != 'done':
            ls.state = 'locked'


def _apply_topic_locks(topic_statuses: list[TopicStatus]) -> None:
    """Темы, идущие после первой не-done, становятся locked."""
    seen_unfinished = False
    for ts in topic_statuses:
        if seen_unfinished and ts.state != 'done':
            ts.state = 'locked'
            _lock_topic_lessons(ts)
            continue
        if ts.state != 'done':
            seen_unfinished = True


def _topic_visible_to(topic: Topic, role_ids: set[int]) -> bool:
    """Тема видна, если у неё не заданы роли (наследует курс) либо роли пересекаются."""
    topic_role_ids = {r.id for r in topic.roles.all()}
    if not topic_role_ids:
        return True
    return bool(topic_role_ids & role_ids)


def build_user_progress(user, courses: Iterable[Course], full_access: bool = False) -> list[CourseStatus]:
    """
    Возвращает список CourseStatus в порядке, в котором сотрудник должен их проходить.
    Последовательные локи: курс N+1 locked пока курс N не done.
    Темы фильтруются по ролям пользователя (Topic.roles).

    full_access=True: все темы видны, ничего не блокируется (всё открыто).
    """
    courses = list(courses)
    if not courses:
        return []

    profile = getattr(user, 'profile', None)
    role_ids: set[int] = set(profile.roles.values_list('id', flat=True)) if profile else set()

    enrollments = {
        e.course_id: e
        for e in Enrollment.objects.filter(user=user, course__in=courses)
    }

    completed_lesson_ids: set[int] = set(
        LessonProgress.objects
        .filter(enrollment__user=user, is_completed=True)
        .values_list('lesson_id', flat=True)
    )

    result: list[CourseStatus] = []
    seen_unfinished_course = False

    for course in courses:
        topics_qs = [
            t for t in course.topics.all().prefetch_related(
                'roles',
                Prefetch('lessons', queryset=Lesson.objects.filter(is_published=True)),
            )
            if full_access or _topic_visible_to(t, role_ids)
        ]
        topic_statuses = [_topic_status(t, completed_lesson_ids) for t in topics_qs]
        if full_access:
            # Снимаем блокировки уроков — всё открыто.
            for ts in topic_statuses:
                for ls in ts.lessons:
                    if ls.state == 'locked':
                        ls.state = 'current'
        else:
            _apply_topic_locks(topic_statuses)

        total_topics = len(topic_statuses)
        completed_topics = sum(1 for t in topic_statuses if t.state == 'done')

        if total_topics == 0:
            course_state = 'done'
        elif completed_topics == total_topics:
            course_state = 'done'
        else:
            course_state = 'current'

        if not full_access and seen_unfinished_course and course_state != 'done':
            course_state = 'locked'
            for ts in topic_statuses:
                ts.state = 'locked'
                _lock_topic_lessons(ts)

        if course_state != 'done':
            seen_unfinished_course = True

        result.append(CourseStatus(
            course=course,
            enrollment=enrollments.get(course.id),
            state=course_state,
            topics=topic_statuses,
            completed_topics=completed_topics,
            total_topics=total_topics,
        ))

    return result


def overall_progress(course_statuses: list[CourseStatus]) -> tuple[int, int, int, int]:
    """Возвращает (done_topics, in_progress_topics, locked_topics, total_topics)."""
    done = in_progress = locked = total = 0
    for cs in course_statuses:
        for ts in cs.topics:
            total += 1
            if ts.state == 'done':
                done += 1
            elif ts.state == 'locked':
                locked += 1
            else:
                in_progress += 1
    return done, in_progress, locked, total


def find_next_lesson(course_statuses: list[CourseStatus]) -> Lesson | None:
    """Первый незавершённый урок в первой незавершённой теме первого незавершённого курса."""
    for cs in course_statuses:
        if cs.state == 'locked':
            continue
        for ts in cs.topics:
            if ts.state in ('locked', 'done'):
                continue
            for ls in ts.lessons:
                if ls.state == 'current':
                    return ls.lesson
    return None
