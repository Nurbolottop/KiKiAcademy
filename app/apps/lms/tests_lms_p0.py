"""Базовые тесты LMS: прогресс, последовательная разблокировка, доступ к
пройденному, результаты квиза и доступ по ролям. Запуск:

    python manage.py test apps.lms --settings=core.settings.test
"""
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.lms.models import (
    Answer,
    Course,
    Enrollment,
    Lesson,
    LessonBlock,
    LessonProgress,
    Question,
    Role,
    RoleCourse,
    Topic,
    UserProfile,
)
from apps.lms.services import build_user_progress, find_next_lesson


def _quiz_with_answer(lesson):
    q = Question.objects.create(lesson=lesson, text='2+2?', order=1)
    right = Answer.objects.create(question=q, text='4', is_correct=True, order=1)
    Answer.objects.create(question=q, text='5', is_correct=False, order=2)
    return q, right


class BaseLMSData(TestCase):
    def setUp(self):
        # Роли засеяны миграцией 0002_seed_roles — берём существующую.
        self.role = Role.objects.get(code=Role.Code.CLEANER)
        self.user = User.objects.create_user(phone='+996700000001', password='pass12345')
        self.profile = UserProfile.objects.create(user=self.user)

        self.course = Course.objects.create(title='Курс A', order=1)
        RoleCourse.objects.create(role=self.role, course=self.course)

        self.topic = Topic.objects.create(course=self.course, title='Тема 1', order=1)
        self.l1 = Lesson.objects.create(topic=self.topic, title='Урок 1', order=1, kind=Lesson.Kind.CONTENT)
        self.l2 = Lesson.objects.create(topic=self.topic, title='Тест', order=2, kind=Lesson.Kind.QUIZ)
        self.q, self.right = _quiz_with_answer(self.l2)

        # Назначаем роль -> сигнал создаст Enrollment
        self.profile.roles.add(self.role)
        self.enrollment = Enrollment.objects.get(user=self.user, course=self.course)


class ProgressServiceTests(BaseLMSData):
    def test_first_lesson_current_rest_locked(self):
        statuses = build_user_progress(self.user, [self.course])
        lessons = statuses[0].topics[0].lessons
        self.assertEqual(lessons[0].state, 'current')
        self.assertEqual(lessons[1].state, 'locked')
        self.assertTrue(lessons[0].accessible)
        self.assertFalse(lessons[1].accessible)

    def test_passed_lesson_stays_accessible(self):
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.l1, is_completed=True)
        statuses = build_user_progress(self.user, [self.course])
        lessons = statuses[0].topics[0].lessons
        self.assertEqual(lessons[0].state, 'done')
        self.assertTrue(lessons[0].accessible)  # пройденный остаётся доступным
        self.assertEqual(lessons[1].state, 'current')

    def test_find_next_lesson(self):
        self.assertEqual(find_next_lesson(build_user_progress(self.user, [self.course])), self.l1)
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.l1, is_completed=True)
        self.assertEqual(find_next_lesson(build_user_progress(self.user, [self.course])), self.l2)

    def test_course_locked_until_previous_done(self):
        course_b = Course.objects.create(title='Курс B', order=2)
        RoleCourse.objects.create(role=self.role, course=course_b)
        tb = Topic.objects.create(course=course_b, title='Тема B', order=1)
        Lesson.objects.create(topic=tb, title='Урок B', order=1)
        self.profile.roles.add(self.role)  # повторный add — без дублей

        statuses = build_user_progress(self.user, list(Course.objects.order_by('order')))
        self.assertEqual(statuses[0].state, 'current')
        self.assertEqual(statuses[1].state, 'locked')
        self.assertTrue(all(ls.state == 'locked' for ls in statuses[1].topics[0].lessons))


class QuizSubmitTests(BaseLMSData):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.url = reverse('lesson_quiz_submit', args=[self.l2.id])

    def test_pass_marks_completed_and_records_score(self):
        resp = self.client.post(self.url, {f'q_{self.q.id}': str(self.right.id)})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['passed'])
        self.assertEqual(data['score_pct'], 100)
        lp = LessonProgress.objects.get(enrollment=self.enrollment, lesson=self.l2)
        self.assertTrue(lp.is_completed)
        self.assertEqual(lp.score_pct, 100)
        self.assertEqual(lp.attempts, 1)

    def test_fail_records_attempt_but_not_completed(self):
        wrong = self.q.answers.get(is_correct=False)
        resp = self.client.post(self.url, {f'q_{self.q.id}': str(wrong.id)})
        data = resp.json()
        self.assertFalse(data['passed'])
        lp = LessonProgress.objects.get(enrollment=self.enrollment, lesson=self.l2)
        self.assertFalse(lp.is_completed)
        self.assertEqual(lp.score_pct, 0)
        self.assertEqual(lp.attempts, 1)

    def test_retake_after_pass_keeps_completed(self):
        self.client.post(self.url, {f'q_{self.q.id}': str(self.right.id)})
        wrong = self.q.answers.get(is_correct=False)
        self.client.post(self.url, {f'q_{self.q.id}': str(wrong.id)})  # пересдача с ошибкой
        lp = LessonProgress.objects.get(enrollment=self.enrollment, lesson=self.l2)
        self.assertTrue(lp.is_completed)   # остаётся пройденным
        self.assertEqual(lp.attempts, 2)   # попытка засчитана


class AccessControlTests(BaseLMSData):
    def test_user_without_role_has_no_access(self):
        other = User.objects.create_user(phone='+996700000002', password='pass12345')
        UserProfile.objects.create(user=other)
        self.client.force_login(other)
        resp = self.client.get(reverse('lesson_view', args=[self.l1.id]))
        self.assertEqual(resp.status_code, 403)

    def test_user_with_role_can_open_lesson(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('lesson_view', args=[self.l1.id]))
        self.assertEqual(resp.status_code, 200)

    def test_passed_quiz_remains_openable(self):
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.l2, is_completed=True)
        self.client.force_login(self.user)
        resp = self.client.get(reverse('lesson_view', args=[self.l2.id]))
        self.assertEqual(resp.status_code, 200)


class TopicRoleAccessTests(TestCase):
    def setUp(self):
        self.cleaner_role = Role.objects.get(code=Role.Code.CLEANER)
        self.manager_role = Role.objects.get(code=Role.Code.MANAGER)
        self.course = Course.objects.create(title='Курс', order=1)
        RoleCourse.objects.create(role=self.cleaner_role, course=self.course)
        RoleCourse.objects.create(role=self.manager_role, course=self.course)

        self.t_all = Topic.objects.create(course=self.course, title='Общая', order=1)
        Lesson.objects.create(topic=self.t_all, title='l1', order=1)
        self.t_mgr = Topic.objects.create(course=self.course, title='Менеджерская', order=2)
        self.mgr_lesson = Lesson.objects.create(topic=self.t_mgr, title='lm', order=1)
        self.t_mgr.roles.add(self.manager_role)  # ограничена ролью MANAGER

        self.cleaner = User.objects.create_user(phone='+996700000010', password='x')
        UserProfile.objects.create(user=self.cleaner).roles.add(self.cleaner_role)
        self.manager = User.objects.create_user(phone='+996700000011', password='x')
        UserProfile.objects.create(user=self.manager).roles.add(self.manager_role)

    def test_cleaner_sees_only_unrestricted_topic(self):
        statuses = build_user_progress(self.cleaner, [self.course])
        titles = [ts.topic.title for ts in statuses[0].topics]
        self.assertIn('Общая', titles)
        self.assertNotIn('Менеджерская', titles)

    def test_manager_sees_all_topics(self):
        statuses = build_user_progress(self.manager, [self.course])
        titles = [ts.topic.title for ts in statuses[0].topics]
        self.assertIn('Общая', titles)
        self.assertIn('Менеджерская', titles)

    def test_role_restricted_lesson_access(self):
        from apps.lms.views import _user_has_access
        self.assertFalse(_user_has_access(self.cleaner, self.mgr_lesson))
        self.assertTrue(_user_has_access(self.manager, self.mgr_lesson))


class SeedCleanerCurriculumTests(TestCase):
    def test_creates_structure_and_is_idempotent(self):
        call_command('seed_cleaner_curriculum', verbosity=0)
        course = Course.objects.get(title='Обучение клинера')
        # 8 этапов = 8 тем
        self.assertEqual(course.topics.count(), 8)
        # Назначен роли клинера
        cleaner = Role.objects.get(code=Role.Code.CLEANER)
        self.assertTrue(RoleCourse.objects.filter(role=cleaner, course=course).exists())
        # ЭТАП 1 наполнен общими стандартами (есть текстовые блоки)
        stage1 = course.topics.get(title__startswith='ЭТАП 1')
        self.assertTrue(
            LessonBlock.objects.filter(lesson__topic=stage1, kind=LessonBlock.Kind.TEXT).exists()
        )
        lessons_after_first = Lesson.objects.count()

        # Повторный запуск не создаёт дублей
        call_command('seed_cleaner_curriculum', verbosity=0)
        self.assertEqual(Course.objects.filter(title='Обучение клинера').count(), 1)
        self.assertEqual(Lesson.objects.count(), lessons_after_first)
