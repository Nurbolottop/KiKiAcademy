"""Структура обучения для роли «СММ / Мобилограф».

Создаёт курс «Обучение СММ / Мобилографа» с этапами и уроками, привязывает к роли
SMM (создаёт роль, если её нет). Идемпотентна.

    python manage.py seed_smm_curriculum
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, Lesson, Role, RoleCourse, Topic

COURSE_TITLE = 'Обучение СММ / Мобилографа'
COURSE_ICON = '📱'

Q = Lesson.Kind.QUIZ
C = Lesson.Kind.CONTENT

CURRICULUM = [
    ('ЭТАП 1 — Введение', [
        ('Обязанности СММ', C),
        ('Стандарты компании', C),
        ('Бренд компании', C),
        ('Контент политика', C),
        ('Ответственность', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 2 — Контент', [
        ('Виды контента', C),
        ('Контент план', C),
        ('Продающий контент', C),
        ('Имиджевый контент', C),
        ('Развлекательный контент', C),
        ('Контент для рекламы', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 3 — Съемка', [
        ('Съемка до/после', C),
        ('Съемка объектов', C),
        ('Съемка сотрудников', C),
        ('Работа со светом', C),
        ('Работа с камерой', C),
        ('Съемка Reels', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 4 — Монтаж', [
        ('Базовый монтаж', C),
        ('Музыка', C),
        ('Субтитры', C),
        ('Переходы', C),
        ('Цветокоррекция', C),
        ('Экспорт видео', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 5 — Социальные сети', [
        ('Instagram', C),
        ('TikTok', C),
        ('YouTube Shorts', C),
        ('Telegram', C),
        ('Публикация контента', C),
        ('Работа с комментариями', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 6 — Маркетинг', [
        ('Анализ конкурентов', C),
        ('Целевая аудитория', C),
        ('Воронка контента', C),
        ('Удержание аудитории', C),
        ('Привлечение клиентов', C),
        ('Продвижение услуг', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 7 — Работа с клиентами', [
        ('Ответы в Direct', C),
        ('Обработка заявок', C),
        ('Работа с отзывами', C),
        ('Негативные комментарии', C),
        ('Передача заявок оператору', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 8 — Работа с CRM', [
        ('Загрузка контента', C),
        ('Отчеты', C),
        ('Аналитика', C),
        ('Контроль заявок', C),
        ('Комментарии', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 9 — Ежедневный отчет', [
        ('Количество публикаций', C),
        ('Охваты', C),
        ('Просмотры', C),
        ('Заявки', C),
        ('Отчеты по рекламе', C),
        ('Итоги рабочего дня', C),
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
        ('Получение статуса СММ / Мобилографа', C),
    ]),
]


class Command(BaseCommand):
    help = 'Создаёт структуру обучения СММ/Мобилографа (11 этапов) и привязывает к роли SMM.'

    @transaction.atomic
    def handle(self, *args, **options):
        course, created = Course.objects.get_or_create(
            title=COURSE_TITLE,
            defaults={'icon': COURSE_ICON, 'order': 5,
                      'description': 'Программа обучения СММ / мобилографа: контент, съёмка, '
                                     'монтаж, соцсети, маркетинг, работа с клиентами, CRM и '
                                     'отчётность.'},
        )
        self.stdout.write(('Создан' if created else 'Найден') + f' курс: {course.title}')

        role, _ = Role.objects.get_or_create(
            code=Role.Code.SMM,
            defaults={'title': 'СММ / Мобилограф', 'is_learning_participant': True})
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
