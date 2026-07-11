"""Подготавливает структуру обучения для роли «Оператор».

Создаёт курс «Обучение оператора» с этапами (темами) и пунктами (уроками),
привязывает к роли OPERATOR. Контент уроков наполняется отдельными командами
seed_operator_stageN_content. Идемпотентна.

    python manage.py seed_operator_curriculum
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, Lesson, Role, RoleCourse, Topic

COURSE_TITLE = 'Обучение оператора'
COURSE_ICON = '🎧'

Q = Lesson.Kind.QUIZ
C = Lesson.Kind.CONTENT

# (Название этапа, [ (название урока, тип), ... ])
CURRICULUM = [
    ('ЭТАП 1 — Введение', [
        ('Обязанности оператора', C),
        ('Стандарты компании', C),
        ('Ответственность', C),
        ('Коммуникация с клиентом', C),
        ('Стандарты сервиса', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 2 — Работа с клиентом', [
        ('Приветствие клиента', C),
        ('Выявление потребностей', C),
        ('Правильная речь', C),
        ('Работа с возражениями', C),
        ('Конфликтные ситуации', C),
        ('VIP клиенты', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 3 — Продажи', [
        ('Продажа услуг', C),
        ('Дополнительные продажи', C),
        ('Апселл услуг', C),
        ('Работа по скрипту', C),
        ('Закрытие клиента', C),
        ('Повторные продажи', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 4 — Услуги компании', [
        ('Влажная уборка', C),
        ('Генеральная уборка', C),
        ('После ремонта', C),
        ('После квартирантов', C),
        ('VIP уборка', C),
        ('Химчистка мебели', C),
        ('Мытье окон', C),
        ('Уборка кухни', C),
        ('Уборка санузла', C),
        ('Уборка офисов', C),
        ('Отличия услуг', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 5 — Расчет стоимости', [
        ('Расчет квадратуры', C),
        ('Расчет стоимости услуг', C),
        ('Дополнительные услуги', C),
        ('Скидки', C),
        ('Минимальный чек', C),
        ('Финальная стоимость', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 7 — Работа с заявками', [
        ('Instagram заявки', C),
        ('WhatsApp заявки', C),
        ('Telegram заявки', C),
        ('Телефонные звонки', C),
        ('Сайт заявки', C),
        ('Повторные обращения', C),
        ('Тест', Q),
    ]),
    ('ЭТАП 8 — Документы и отчеты', [
        ('Отчет по заявкам', C),
        ('Отчет по продажам', C),
        ('Отчет по клиентам', C),
        ('Проблемные заявки', C),
        ('Ежедневный отчет', C),
    ]),
    ('ЭТАП 10 — Финальная аттестация', [
        ('Общий экзамен', Q),
        ('Практическая проверка', C),
        ('Проверка руководителем', C),
        ('Получение статуса оператора', C),
    ]),
]


class Command(BaseCommand):
    help = 'Создаёт структуру обучения оператора (этапы/темы) и привязывает к роли OPERATOR.'

    @transaction.atomic
    def handle(self, *args, **options):
        course, created = Course.objects.get_or_create(
            title=COURSE_TITLE,
            defaults={'icon': COURSE_ICON, 'order': 2,
                      'description': 'Программа обучения оператора: работа с клиентами, '
                                     'продажи, услуги, расчёт стоимости, заявки и отчётность.'},
        )
        self.stdout.write(('Создан' if created else 'Найден') + f' курс: {course.title}')

        operator = Role.objects.filter(code=Role.Code.OPERATOR).first()
        if operator:
            RoleCourse.objects.get_or_create(role=operator, course=course,
                                             defaults={'is_required': True})
            self.stdout.write(f'Курс назначен роли: {operator.title}')
        else:
            self.stdout.write(self.style.WARNING('Роль OPERATOR не найдена — курс не назначен.'))

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
