"""Наполняет ЭТАП 4 — Салфетки курса «Обучение клинера».

Структура: КАЖДЫЙ вид салфетки = отдельная тема (урок). Материалы — реальные
(Cleaning KIKI + офиц. данные о микрофибре). Команда удаляет старые placeholder-уроки,
пересобирает уроки-салфетки и тест. Новые салфетки добавляются в список CLOTHS.

    python manage.py seed_stage4_content

ФОТО: блок IMAGE берёт файл из media/lessons/images/ (офиц. сайт UrbanClean).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Answer, Course, Lesson, LessonBlock, Question, Topic

COURSE_TITLE = 'Обучение клинера'
TOPIC_TITLE = 'ЭТАП 4 — Салфетки'


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


def chip(color, label):
    return (f'<span style="display:inline-block;width:14px;height:14px;border-radius:4px;'
            f'background:{color};vertical-align:middle;margin-right:8px;border:1px solid #00000022;">'
            f'</span>{label}')


# Каждый вид салфетки = отдельная тема (урок). (Название, [ (тип_блока, payload), ... ]).
CLOTHS = [
    ('Универсальная микрофибра', [
        ('image', ('lessons/images/microfiber-universal-blue.jpg',
                   'Универсальная микрофибровая салфетка (UrbanClean)')),
        ('text',
         '<h3>🧽 Что это</h3>'
         '<p>Главная рабочая салфетка клинера — <strong>универсальная микрофибра</strong>. '
         'Подходит почти для всего: пыль, влажная протирка, стёкла, мебель, техника.</p>'
         + li('Собирает пыль и грязь <strong>даже без химии</strong> — одной водой',
              'Не оставляет <strong>ворса и разводов</strong>',
              'Волокно тоньше человеческого волоса — «цепляет» мельчайшую пыль и бактерии',
              'Выдерживает <strong>500+ стирок</strong> при правильном уходе')),
        ('text',
         '<h3>🏠 Зоны применения (комнаты)</h3>'
         + li('Спальня', 'Гостиная', 'Детская', 'Коридор')),
        ('text',
         '<h3>📍 Что протираем этой салфеткой</h3>'
         + li('<strong>Стёкла и зеркала</strong>', '<strong>Радиаторы отопления</strong>',
              '<strong>Шкафы</strong>', '<strong>Двери</strong>',
              '<strong>Люстры</strong>', '<strong>Поверхности</strong> (полки, столы, подоконники)')
         + note('После мытья губкой грязь <strong>вытираем этой салфеткой</strong> — '
                'она убирает остатки и доводит поверхность до чистоты без разводов.')),
        ('image', ('lessons/images/microfiber-colors.jpg',
                   'Микрофибра разных цветов — под разные зоны')),
        ('text',
         '<h3>🎨 Цвет = зона</h3>'
         '<p>Микрофибра бывает разных цветов, чтобы <strong>не переносить грязь и бактерии</strong> '
         'между зонами. Общая схема:</p>'
         + li(chip('#3b82f6', '<strong>Синяя</strong> — стёкла, зеркала, пыль, общие поверхности'),
              chip('#22c55e', '<strong>Зелёная</strong> — кухня, зоны с едой'),
              chip('#eab308', '<strong>Жёлтая</strong> — раковины, ванна, санузел'),
              chip('#ef4444', '<strong>Красная</strong> — унитаз, зона высокого риска'))
         + note('Точные цвета уточняйте по схеме Cleaning KIKI. Главное — салфетку санузла '
                'никогда не использовать на кухне и мебели.')),

        # ── Цветные микрофибры под зоны (внутри этой же темы) ──────────────────
        ('text',
         '<h3>🔴 Красная — санузел 🛁</h3>'
         '<p>Красная микрофибра — <strong>только для санузла</strong> (туалет и ванна), '
         'это зона высокого риска.</p>'
         + li('Кафель', 'Потолок', 'Раковина', 'Ванна', 'Двери', 'Стиральная машина')),
        ('image', ('lessons/images/microfiber-red.jpg', 'Красная микрофибра — санузел')),
        ('text',
         warn('Красную <strong>никогда</strong> не используем на кухне, мебели и в комнатах — '
              'это перенос бактерий из санузла.')),
        ('text',
         '<h3>🟢 Зелёная — кухня 🍳</h3>'
         '<p>Зелёная микрофибра — <strong>только для кухни</strong> (зона контакта с едой).</p>'
         + li('Кухонный гарнитур', 'Микроволновая печь', 'Газовая плита', 'Холодильник',
              'Вытяжка', 'Отопление', 'Стёкла', 'Люстра', 'Двери', 'Выключатели',
              'Обои', 'Потолок')),
        ('image', ('lessons/images/microfiber-green.jpg', 'Зелёная микрофибра — кухня')),
        ('text',
         warn('Зелёную <strong>не используем</strong> в санузле. Цвет = зона, не смешиваем.')),

        ('text',
         '<h3>🧭 Как правильно пользоваться</h3>'
         + li('<strong>Сухая</strong> — для пыли; <strong>слегка влажная</strong> — для уборки',
              'Сложить <strong>вчетверо</strong> — получится 8 чистых рабочих сторон, '
              'переворачивай по мере загрязнения',
              'Средство наносим <strong>на салфетку</strong>, а не на поверхность (особенно техника)',
              'Испачкалась — прополоскать или взять чистую, не размазывать грязь')),
        ('text',
         '<h3>🧺 Уход и стирка</h3>'
         + li('Стирать <strong>без кондиционера</strong> — он забивает волокно, салфетка '
              'перестаёт впитывать',
              'Температура умеренная (до 60°), не кипятить',
              'Стирать <strong>по зонам отдельно</strong> (санузельные — отдельно)',
              'Сушить без сильного нагрева')),
        ('text',
         '<h3>❌ Частые ошибки</h3>'
         + warn(li('Одна салфетка на все зоны — перенос грязи и бактерий',
                   'Работа грязной салфеткой по чистому — разводы',
                   'Кондиционер при стирке — микрофибра «умирает»',
                   'Слишком мокрая салфетка на технике и дереве'))),
        ('text',
         ok('Чистая сухая микрофибра + немного воды решает <strong>80% задач</strong> '
            'по протирке в комнатах. Это твой главный инструмент.')),
    ]),

    ('Гладкая микрофибра для стекла (финиш)', [
        ('image', ('lessons/images/microfiber-glass.jpg',
                   'Гладкая микрофибра для стекла и полировки (UrbanClean)')),
        ('text',
         '<h3>🪟 Что это</h3>'
         '<p>Это <strong>гладкая (стекольная) микрофибра</strong> — отличается от махровой '
         'универсальной. Её задача — <strong>финиш без разводов</strong>: довести уже чистую '
         'поверхность до блеска.</p>'
         + li('Без ворса — не оставляет разводов и ниток',
              'Для стекла, зеркал, глянца, хрома, техники',
              'Подходит для всех поверхностей — но как <strong>завершающий</strong> шаг')),
        ('text',
         '<h3>📍 Главное правило — только по чистому</h3>'
         + warn('Использовать <strong>только на чистых местах</strong>! По грязи и жиру она '
                'забивается и сама оставляет разводы.')
         + note('<strong>Порядок работы:</strong> сначала отрабатываем поверхность <strong>цветными '
                'салфетками</strong> (синяя/зелёная/красная — 3–4 цвета по зонам), убираем грязь, '
                '<strong>и только потом</strong> этой гладкой микрофиброй полируем до блеска.')),
        ('text',
         '<h3>🧭 Как пользоваться</h3>'
         + li('Сухой или <strong>чуть влажной</strong> — для финишной полировки',
              'Движения без пропусков, сверху вниз',
              'Стекло не полировать под прямым солнцем — будут разводы',
              'Держать отдельно и чистой — это «финишный» инструмент')),
        ('text',
         ok('Запомни: <strong>цветные салфетки убирают грязь → гладкая микрофибра наводит '
            'блеск</strong> без разводов.')),
    ]),
]

QUIZ = [
    ('Чем хороша универсальная микрофибра?', [
        ('Собирает пыль и грязь даже без химии, не оставляет разводов и ворса', True),
        ('Работает только с большим количеством химии', False),
        ('Подходит лишь для пола', False),
    ]),
    ('Что протираем универсальной микрофиброй в комнате?', [
        ('Стёкла, зеркала, радиаторы, шкафы, двери, люстры, поверхности', True),
        ('Только унитаз', False),
        ('Только пол', False),
    ]),
    ('Зачем микрофибра разных цветов?', [
        ('Чтобы не переносить грязь и бактерии между зонами', True),
        ('Для красоты', False),
        ('Цвет ни на что не влияет', False),
    ]),
    ('Как правильно сложить салфетку для работы?', [
        ('Вчетверо — получается 8 чистых сторон, переворачивать по мере загрязнения', True),
        ('Скомкать в шар', False),
        ('Работать одной стороной до конца', False),
    ]),
    ('Можно ли стирать микрофибру с кондиционером?', [
        ('Нет — он забивает волокно, салфетка перестаёт впитывать', True),
        ('Да, обязательно', False),
        ('Да, и желательно кипятить', False),
    ]),
    ('Что делает клинер этой салфеткой после мытья губкой?', [
        ('Вытирает остатки грязи и доводит поверхность до чистоты', True),
        ('Выбрасывает салфетку', False),
        ('Ничего не делает', False),
    ]),
    ('Для какой зоны красная салфетка?', [
        ('Туалет и ванна (санузел)', True),
        ('Кухня', False),
        ('Спальня', False),
    ]),
    ('Можно ли красной салфеткой протирать кухню?', [
        ('Нет — это перенос бактерий из санузла', True),
        ('Да, если она чистая', False),
        ('Да, без разницы', False),
    ]),
    ('Для какой зоны зелёная салфетка?', [
        ('Кухня', True),
        ('Санузел', False),
        ('Коридор', False),
    ]),
    ('Чем протираем зелёной салфеткой?', [
        ('Гарнитур, плита, холодильник, вытяжка, микроволновка и т.д.', True),
        ('Унитаз и ванну', False),
        ('Только пол в санузле', False),
    ]),
    ('Для чего гладкая микрофибра для стекла?', [
        ('Финиш без разводов — полировка уже чистой поверхности', True),
        ('Оттереть жир и грязь', False),
        ('Мыть унитаз', False),
    ]),
    ('Когда применяют гладкую (финишную) микрофибру?', [
        ('Только по чистому — после уборки цветными салфетками', True),
        ('Сразу по грязи и жиру', False),
        ('Вместо всех остальных салфеток', False),
    ]),
]


class Command(BaseCommand):
    help = 'Наполняет ЭТАП 4 — Салфетки (каждый вид = тема) и тест.'

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

        keep_titles = [title for title, _ in CLOTHS]

        # Удаляем старые placeholder-уроки (не в новой структуре, не тест).
        stale = Lesson.objects.filter(topic=topic, kind=Lesson.Kind.CONTENT).exclude(
            title__in=keep_titles)
        stale_titles = list(stale.values_list('title', flat=True))
        stale.delete()
        if stale_titles:
            self.stdout.write('Удалено старых уроков: ' + ', '.join(stale_titles))

        blocks_n = 0
        for order, (title, items) in enumerate(CLOTHS, start=1):
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
            quiz.order = len(CLOTHS) + 1
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
            f'Готово. Салфеток-тем: {len(CLOTHS)}, блоков: {blocks_n}, вопросов: {q_n}.'
        ))
