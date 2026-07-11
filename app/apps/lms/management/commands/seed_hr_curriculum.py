"""Структура обучения для роли «HR менеджер».

Создаёт курс «Обучение HR менеджера» с этапами и уроками, привязывает к роли HR
(создаёт роль, если её нет). Идемпотентна.

    python manage.py seed_hr_curriculum
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, Lesson, Role, RoleCourse, Topic

COURSE_TITLE = 'Обучение HR менеджера'
COURSE_ICON = '👥'

Q = Lesson.Kind.QUIZ
C = Lesson.Kind.CONTENT

CURRICULUM = [
    ('ЭТАП 1 — Введение', [
        ('Обязанности HR менеджера', C),
        ('Стандарты компании', C),
        ('Ответственность', C),
        ('Коммуникация внутри компании', C),
        ('Работа с персоналом', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 2 — Поиск сотрудников', [
        ('Поиск кандидатов', C),
        ('Площадки для поиска', C),
        ('Работа с откликами', C),
        ('Фильтрация кандидатов', C),
        ('Первичный отбор', C),
        ('База кандидатов', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 3 — Собеседование', [
        ('Проведение собеседования', C),
        ('Вопросы кандидатам', C),
        ('Проверка адекватности', C),
        ('Проверка ответственности', C),
        ('Проверка опыта', C),
        ('Финальное решение', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 4 — Найм сотрудников', [
        ('Оформление сотрудников', C),
        ('Добавление в систему', C),
        ('Подготовка документов', C),
        ('Передача информации менеджеру', C),
        ('Назначение стажировки', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 5 — Адаптация сотрудников', [
        ('Онбординг', C),
        ('Ознакомление с компанией', C),
        ('Назначение обучения', C),
        ('Контроль прохождения курсов', C),
        ('Проверка стажеров', C),
        ('Контроль первых объектов', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 6 — Контроль персонала', [
        ('Посещаемость', C),
        ('Дисциплина', C),
        ('Опоздания', C),
        ('Жалобы на сотрудников', C),
        ('Конфликты внутри команды', C),
        ('Мотивация для сотрудников', C),
        ('Увольнение сотрудников', C),
        ('Фидбек от сотрудников', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 7 — Работа с CRM системой', [
        ('Добавление сотрудников', C),
        ('Статусы сотрудников', C),
        ('Проверка данных', C),
        ('Документы сотрудников', C),
        ('История сотрудника', C),
        ('Отчеты', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 8 — Документы', [
        ('Договоры', C),
        ('Анкеты', C),
        ('Паспортные данные', C),
        ('Внутренние документы', C),
        ('Политики компании', C),
        ('Регламенты', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 9 — Отчетность', [
        ('Отчет по найму', C),
        ('Отчет по стажерам', C),
        ('Отчет по увольнениям', C),
        ('Отчет по персоналу', C),
        ('Проблемные сотрудники', C),
        ('Ежедневный отчет', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 10 — База знаний', [
        ('Инструкции', C),
        ('Регламенты', C),
        ('FAQ', C),
        ('Обновления', C),
        ('Документы', C),
    ]),
    ('ЭТАП 11 — Финальная аттестация', [
        ('Общий экзамен', Q),
        ('Практическая проверка', C),
        ('Проверка руководителем', C),
        ('Получение статуса HR менеджера', C),
    ]),
]


class Command(BaseCommand):
    help = 'Создаёт структуру обучения HR менеджера (11 этапов) и привязывает к роли HR.'

    @transaction.atomic
    def handle(self, *args, **options):
        course, created = Course.objects.get_or_create(
            title=COURSE_TITLE,
            defaults={'icon': COURSE_ICON, 'order': 4,
                      'description': 'Программа обучения HR менеджера: поиск и найм сотрудников, '
                                     'собеседования, адаптация, контроль персонала, CRM, документы '
                                     'и отчётность.'},
        )
        self.stdout.write(('Создан' if created else 'Найден') + f' курс: {course.title}')

        role, _ = Role.objects.get_or_create(
            code=Role.Code.HR, defaults={'title': 'HR менеджер', 'is_learning_participant': True})
        RoleCourse.objects.get_or_create(role=role, course=course, defaults={'is_required': True})
        self.stdout.write(f'Курс назначен роли: {role.title}')

        topics_n = lessons_n = 0
        for t_order, (stage_title, lessons) in enumerate(CURRICULUM, start=1):
            topic, t_created = Topic.objects.get_or_create(
                course=course, title=stage_title, defaults={'order': t_order},
            )
            if not t_created and topic.order != t_order:
                topic.order = t_order
                topic.save(update_fields=['order'])
            topics_n += int(t_created)

            for l_order, (lesson_title, kind) in enumerate(lessons, start=1):
                lesson, l_created = Lesson.objects.get_or_create(
                    topic=topic, title=lesson_title,
                    defaults={'order': l_order, 'kind': kind, 'is_published': True},
                )
                if not l_created and lesson.order != l_order:
                    lesson.order = l_order
                    lesson.save(update_fields=['order'])
                lessons_n += int(l_created)

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Новых тем: {topics_n}, уроков: {lessons_n}.'
        ))
