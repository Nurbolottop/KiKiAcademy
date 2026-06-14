"""Наполняет ЭТАП 3 — Инвентарь курса «Обучение клинера».

Структура: КАЖДЫЙ инструмент = отдельная тема (урок). Материалы реальные
(Cleaning KIKI + офиц. данные). Команда удаляет старые placeholder-уроки,
пересобирает уроки-инструменты и тест. Новые инструменты добавляются в TOOLS.

    python manage.py seed_stage3_content

ФОТО: блок IMAGE берёт файл из media/lessons/images/ (офиц. источники).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Answer, Course, Lesson, LessonBlock, Question, Topic

COURSE_TITLE = 'Обучение клинера'
TOPIC_TITLE = 'ЭТАП 3 — Инвентарь'


def _callout(html, color):
    return (f'<div style="background:{color}1f;border-left:4px solid {color};'
            f'padding:12px 16px;border-radius:10px;margin:14px 0;">{html}</div>')


def warn(html):
    return _callout('⚠️ ' + html, '#ef4444')


def note(html):
    return _callout('ℹ️ ' + html, '#6c63ff')


def ok(html):
    return _callout('✅ ' + html, '#22c55e')


def li(*items):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'


# Каждый инструмент = отдельная тема (урок). (Название, [ (тип_блока, payload), ... ]).
TOOLS = [
    ('Пароочиститель (Karcher)', [
        ('image', ('lessons/images/steam-cleaner-karcher.jpg',
                   'Пароочиститель Karcher SC 2 с насадками')),
        ('text',
         '<h3>💨 Что это</h3>'
         '<p>Пароочиститель чистит и <strong>дезинфицирует горячим паром</strong>, '
         '<strong>без химии</strong>. Отлично берёт жир, налёт и грязь в швах и труднодоступных '
         'местах.</p>'),
        ('text',
         '<h3>🔧 Как пользоваться</h3>'
         + li('Заливаем <strong>только фильтрованную воду</strong>. '
              '<strong>Средство/химию добавлять НЕЛЬЗЯ.</strong>',
              'Нагреваем <strong>5–8 минут</strong>.',
              'Когда <strong>жёлтая лампочка погаснет</strong> — вода нагрелась, только тогда '
              'начинаем работать.',
              'В пистолете сначала может быть вода — <strong>спускаем её в ведро</strong>, '
              'и работаем только когда пошёл пар 💨.')),
        ('image', ('lessons/images/steam-cleaner-karcher-use.jpg',
                   'Чистка паром — стеклокерамика/поверхность')),
        ('text',
         '<h3>📍 Где применяется</h3>'
         + li('Отопление (батареи, радиаторы)',
              'Оконные рамы',
              'Углы и щели газовой плиты',
              'Жирные места',
              'Хрустальная люстра',
              'Швы и углы кафеля')),
        ('text',
         '<h3>⚠️ Безопасность</h3>'
         + warn('Пар <strong>очень горячий</strong> — опасность ожога. Не направлять на людей '
                'и на себя, не трогать сопло.')
         + note('Не применять на поверхностях, боящихся высокой температуры (некоторый пластик, '
                'деликатные лаки), без проверки на незаметном участке.')),
        ('text',
         '<h3>🧼 Уход</h3>'
         + li('Только <strong>фильтрованная вода</strong> — защита от накипи',
              'После работы дать остыть и слить воду',
              'Насадки промыть и просушить')),
    ]),
]

QUIZ = [
    ('Что заливают в пароочиститель?', [
        ('Только фильтрованную воду, без средства', True),
        ('Воду с чистящим средством', False),
        ('Любую воду и химию', False),
    ]),
    ('Когда можно начинать работу пароочистителем?', [
        ('Когда нагрелся (жёлтая лампочка погасла) и пошёл пар', True),
        ('Сразу после включения', False),
        ('Когда из пистолета течёт вода', False),
    ]),
    ('Что делают, если из пистолета идёт вода, а не пар?', [
        ('Спускают воду в ведро и ждут пар', True),
        ('Работают прямо так', False),
        ('Выключают прибор насовсем', False),
    ]),
    ('Где применяют пароочиститель?', [
        ('Швы кафеля, батареи, рамы окон, жирные места, люстра', True),
        ('Только пол', False),
        ('Только мягкую мебель', False),
    ]),
    ('Главная опасность пароочистителя?', [
        ('Горячий пар — ожог; не направлять на людей', True),
        ('Он бьётся током от воды', False),
        ('Никакой опасности нет', False),
    ]),
]


class Command(BaseCommand):
    help = 'Наполняет ЭТАП 3 — Инвентарь (каждый инструмент = тема) и тест.'

    @transaction.atomic
    def handle(self, *args, **options):
        course = Course.objects.filter(title=COURSE_TITLE).first()
        if not course:
            self.stdout.write(self.style.WARNING(f'Курс «{COURSE_TITLE}» не найден.'))
            return
        topic = Topic.objects.filter(course=course, title=TOPIC_TITLE).first()
        if not topic:
            self.stdout.write(self.style.WARNING(f'Этап «{TOPIC_TITLE}» не найден.'))
            return

        keep_titles = [title for title, _ in TOOLS]

        # Удаляем старые placeholder-уроки (не в новой структуре, не тест).
        stale = Lesson.objects.filter(topic=topic, kind=Lesson.Kind.CONTENT).exclude(
            title__in=keep_titles)
        stale_titles = list(stale.values_list('title', flat=True))
        stale.delete()
        if stale_titles:
            self.stdout.write('Удалено старых уроков: ' + ', '.join(stale_titles))

        blocks_n = 0
        for order, (title, items) in enumerate(TOOLS, start=1):
            lesson, _ = Lesson.objects.get_or_create(
                topic=topic, title=title,
                defaults={'kind': Lesson.Kind.CONTENT, 'order': order})
            lesson.kind = Lesson.Kind.CONTENT
            lesson.order = order
            lesson.save(update_fields=['kind', 'order'])
            lesson.blocks.all().delete()
            for b_order, (kind, payload) in enumerate(items, start=1):
                if kind == 'text':
                    LessonBlock.objects.create(lesson=lesson, kind=LessonBlock.Kind.TEXT,
                                               order=b_order, text=payload)
                elif kind == 'image':
                    if isinstance(payload, tuple):
                        image_path, caption = payload
                    else:
                        image_path, caption = '', payload
                    block = LessonBlock(lesson=lesson, kind=LessonBlock.Kind.IMAGE,
                                        order=b_order, caption=caption)
                    if image_path:
                        block.image = image_path
                    block.save()
                elif kind == 'video':
                    url, caption = payload
                    LessonBlock.objects.create(lesson=lesson, kind=LessonBlock.Kind.VIDEO,
                                               order=b_order, video_url=url, caption=caption)
                blocks_n += 1
            self.stdout.write(f'  ✓ {title} ({len(items)} блоков)')

        quiz = Lesson.objects.filter(topic=topic, title='Тест', kind=Lesson.Kind.QUIZ).first()
        q_n = 0
        if quiz:
            quiz.order = len(TOOLS) + 1
            quiz.save(update_fields=['order'])
            quiz.questions.all().delete()
            for q_order, (q_text, answers) in enumerate(QUIZ, start=1):
                question = Question.objects.create(lesson=quiz, text=q_text, order=q_order)
                for a_order, (a_text, is_correct) in enumerate(answers, start=1):
                    Answer.objects.create(question=question, text=a_text,
                                          is_correct=is_correct, order=a_order)
                q_n += 1
            self.stdout.write(f'  ✓ Тест: {q_n} вопросов')

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Инструментов-тем: {len(TOOLS)}, блоков: {blocks_n}, вопросов: {q_n}.'
        ))
