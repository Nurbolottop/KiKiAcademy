"""Наполняет ЭТАП 2 — Средства курса «Обучение клинера».

Всё в ОДНОЙ теме «Виды химии»: теория (pH, кислотные/щелочные/дезинфицирующие,
что нельзя смешивать, безопасность, хранение) + реальные средства (Bingo и далее)
блоками внутри. Старые мелкие placeholder-уроки удаляются. Идемпотентна.

    python manage.py seed_stage2_content

ФОТО СРЕДСТВ: блок IMAGE берёт файл из app/media/lessons/images/ (с офиц./розничных
сайтов; Claude не генерирует фото товара).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Answer, Course, Lesson, LessonBlock, Question, Topic

COURSE_TITLE = 'Обучение клинера'
TOPIC_TITLE = 'ЭТАП 2 — Средства'
LESSON_TITLE = 'Виды химии'


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


# Все блоки одной темы по порядку.
# Тип блока: 'text' (html) | 'image' ((путь_в_MEDIA, подпись) | строка-подпись) | 'video' ((url, подпись))
BLOCKS = [
    # ── ТЕОРИЯ ───────────────────────────────────────────────────────────────
    ('text',
     '<h3>📋 Зачем разбираться в химии</h3>'
     '<p>Профессиональная химия экономит силы, но только при правильном применении. '
     'Неверное средство либо не справится, либо испортит поверхность. Клинер обязан '
     'знать, <strong>что и для чего</strong> он берёт.</p>'),
    ('text',
     '<h3>🧪 Основные группы средств</h3>'
     + li('<strong>Универсальные</strong> — повседневная уборка (полы, стены, мебель)',
          '<strong>Для стекла и зеркал</strong> — без разводов',
          '<strong>Для сантехники</strong> — кислотные, против налёта и ржавчины',
          '<strong>Для кухни и жира</strong> — щелочные обезжириватели',
          '<strong>Дезинфицирующие</strong> — уничтожают микробы и бактерии',
          '<strong>Полироли и защитные</strong> — мебель, нержавейка, дерево')),
    ('text',
     '<h3>⚗️ Что такое pH</h3>'
     '<p>pH — шкала от <strong>0 до 14</strong>: кислотное средство или щелочное. От pH '
     'зависит, какое загрязнение средство растворяет и где его можно применять.</p>'
     + li('<strong>0–6 — кислотные:</strong> налёт, ржавчина, известь, мочевой камень',
          '<strong>7 — нейтральные:</strong> деликатные поверхности, ежедневная уборка',
          '<strong>8–14 — щелочные:</strong> жир, масляные и белковые загрязнения')
     + note('Чем дальше pH от 7 — тем <strong>агрессивнее</strong> средство.')),
    ('text',
     '<h3>🧪 Кислотные средства (pH 0–6)</h3>'
     '<p>Растворяют минеральные загрязнения: известковый налёт, ржавчину, мочевой камень, '
     'остатки затирки. Применяют в санузле, на сантехнике и кафеле.</p>'
     + warn('<strong>Нельзя</strong> на натуральном камне (мрамор, гранит), алюминии и '
            'хроме при долгой выдержке — кислота разъедает их.')),
    ('text',
     '<h3>🧪 Щелочные средства (pH 8–14)</h3>'
     '<p>Растворяют жир, масло, нагар и копоть. Основа кухонных обезжиривателей — плита, '
     'вытяжка, духовка, фасады.</p>'
     + warn('<strong>Нельзя</strong> на алюминии (темнеет) и деликатных лакированных '
            'поверхностях без проверки.')),
    ('text',
     '<h3>🦠 Дезинфицирующие средства</h3>'
     '<p>Уничтожают микробы, а не просто удаляют грязь. Унитаз, раковина, кухня, ручки, '
     'выключатели.</p>'
     + note('Сначала <strong>очистка</strong>, потом дезинфекция. Средство должно '
            '<strong>остаться влажным</strong> нужное время — иначе микробы не погибнут.')),
    ('text',
     '<h3>☠️ Что нельзя смешивать</h3>'
     + warn('<strong>Хлорка/отбеливатель + кислота</strong> (средство для сантехники) '
            '= <strong>ядовитый хлор</strong>.')
     + warn('<strong>Хлорка/отбеливатель + аммиак</strong> (средства для стекла) '
            '= <strong>токсичный хлорамин</strong>.')
     + li('Используем <strong>одно средство за раз</strong>',
          'Перед сменой средства — <strong>смыть водой</strong> предыдущее',
          'Никогда не смешиваем в одной ёмкости',
          'Сомневаешься — не смешивай, спроси менеджера')),
    ('text',
     '<h3>🧤 Безопасное использование</h3>'
     + li('Работаем в <strong>перчатках</strong>, при агрессивной химии — защита глаз',
          'Помещение <strong>проветривается</strong>',
          'Концентрат разводим <strong>строго по инструкции</strong>',
          'Новую поверхность — сначала тест на незаметном участке',
          'Попало на кожу/в глаза — обильно промыть водой')),
    ('text',
     '<h3>📦 Хранение химии</h3>'
     + li('В <strong>оригинальной таре с этикеткой</strong>, плотно закрытой',
          'Прохладное место, без солнца и нагрева',
          'Кислоты и хлорсодержащие — <strong>отдельно друг от друга</strong>',
          'Вдали от продуктов, недоступно для детей и животных')
     + warn('Средства без этикетки и просроченные — <strong>не используем</strong>.')),

    # ── НАШИ СРЕДСТВА ─────────────────────────────────────────────────────────
    ('text', '<h2>🧴 Наши средства</h2>'
             '<p>Конкретные средства, с которыми работает клинер Cleaning KIKI.</p>'),

    # Bingo Universal Cream
    ('text', '<h3>Bingo Universal Cream («паста») 😄</h3>'
             '<p>Многоцелевой чистящий крем. Идеален для плитки, сантехники и плиты, '
             'часто на уборке после ремонта.</p>'),
    ('image', ('lessons/images/bingo-universal-cream.jpg',
               'Bingo Krem — универсальный чистящий крем, 750 мл')),
    ('text',
     '<h4>🍳 Кухня</h4>'
     + li('<strong>Плита и духовка:</strong> растворяет пригоревший жир и нагар — нанести, '
          'оставить на 5 минут, затем губкой.',
          '<strong>Раковина и смеситель:</strong> убирает известь и жёлтый налёт, полирует нержавейку.',
          '<strong>Швы плитки:</strong> протереть и почистить щёткой.',
          '<strong>Внутри микроволновки:</strong> снимает брызги жира.')),
    ('text',
     '<h4>🚿 Ванна и туалет</h4>'
     + li('<strong>Ванна, раковина, унитаз:</strong> жёлтый налёт и известь. Акрил — можно, '
          'но не тереть сильно.',
          '<strong>Кран и душ:</strong> полирует хром, убирает водяные пятна.',
          '<strong>Плитка:</strong> мыльный налёт и известь.')),
    ('text',
     '<h4>🛋️ Зал и комнаты</h4>'
     + li('<strong>Кафельный пол:</strong> убирает пятна без разводов — после протереть водой.',
          '<strong>Двери, пластиковый подоконник, ручки:</strong> жёлтые пятна и следы рук.')
     + warn('На <strong>ламинат — НЕЛЬЗЯ</strong>: царапает верхний слой.')),
    ('text',
     '<h4>🛋️ Мягкая мебель — ограниченно</h4>'
     '<p><strong>Обязателен тест:</strong> протереть на незаметном участке, подождать 2 минуты, '
     'применять если цвет не изменился.</p>'
     + li('Кожа и кожзам — <strong>можно</strong>', 'Тканевый диван (кумач) — <strong>нельзя</strong>')),
    ('text',
     '<h4>⛔ Правило «3 НЕЛЬЗЯ»</h4>'
     + warn(li('<strong>Алюминий и окрашенные поверхности</strong> — царапает, снимает краску',
               '<strong>Натуральный камень, мрамор, гранит</strong> — содержит кислоту, разрушает',
               '<strong>Экраны телефона, ноутбука, ТВ</strong> — убивает антибликовый слой'))),
    ('text',
     '<h4>💡 Лайфхаки</h4>'
     + li('Немного на <strong>влажную</strong> губку — на сухую поцарапаешь.',
          'Оставь на <strong>5–10 минут</strong> — пригоревший жир растворится сам.',
          'После мытья <strong>протри водой</strong> — иначе белые разводы.')
     + warn('Работать в <strong>перчатках</strong> — сушит кожу. Хранить от детей и животных.')),
]

# Тест по этапу. Дополняйте при добавлении новых средств.
QUIZ = [
    ('Что показывает шкала pH средства?', [
        ('Кислотное оно или щелочное', True),
        ('Цену средства', False),
        ('Срок годности', False),
    ]),
    ('Каким средством убирают известковый налёт и ржавчину?', [
        ('Кислотным (pH 0–6)', True),
        ('Щелочным (pH 8–14)', False),
        ('Нейтральным (pH 7)', False),
    ]),
    ('Каким средством лучше убирать жир на кухне?', [
        ('Щелочным обезжиривателем', True),
        ('Кислотным средством для сантехники', False),
        ('Средством для стекла', False),
    ]),
    ('Что образуется при смешивании хлорки и кислоты?', [
        ('Ядовитый хлор', True),
        ('Безопасная пена', False),
        ('Более сильное чистящее средство', False),
    ]),
    ('На какой поверхности нельзя применять кислоту?', [
        ('Натуральный камень (мрамор, гранит)', True),
        ('Унитаз', False),
        ('Кафель в санузле', False),
    ]),
    ('Для чего лучше всего подходит Bingo Universal Cream?', [
        ('Плитка, сантехника, плита — пригоревший жир и налёт', True),
        ('Мытьё экранов телефонов и ноутбуков', False),
        ('Полировка мраморных столешниц', False),
    ]),
    ('Как правильно наносить Bingo Universal Cream?', [
        ('Немного на влажную губку, выдержать 5–10 мин, затем смыть водой', True),
        ('На сухую губку и сразу тереть', False),
        ('Налить много и оставить до высыхания', False),
    ]),
    ('Куда нельзя наносить Bingo Universal Cream?', [
        ('Ламинат, мрамор/гранит, экраны, окрашенные поверхности', True),
        ('Кафельная плитка', False),
        ('Нержавеющая раковина', False),
    ]),
]


class Command(BaseCommand):
    help = 'Наполняет ЭТАП 2 — Средства одной темой (теория + реальные средства) и тестом.'

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

        # Удаляем все старые placeholder-уроки, кроме нашей единственной темы и теста.
        stale = Lesson.objects.filter(topic=topic, kind=Lesson.Kind.CONTENT).exclude(
            title=LESSON_TITLE)
        stale_titles = list(stale.values_list('title', flat=True))
        stale.delete()
        if stale_titles:
            self.stdout.write('Удалено старых уроков: ' + ', '.join(stale_titles))

        lesson, _ = Lesson.objects.get_or_create(
            topic=topic, title=LESSON_TITLE,
            defaults={'kind': Lesson.Kind.CONTENT, 'order': 1})
        lesson.kind = Lesson.Kind.CONTENT
        lesson.order = 1
        lesson.save(update_fields=['kind', 'order'])
        lesson.blocks.all().delete()

        blocks_n = 0
        for b_order, (kind, payload) in enumerate(BLOCKS, start=1):
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
        self.stdout.write(f'  ✓ {LESSON_TITLE} ({blocks_n} блоков)')

        quiz = Lesson.objects.filter(topic=topic, title='Тест', kind=Lesson.Kind.QUIZ).first()
        q_n = 0
        if quiz:
            quiz.order = 2
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
            f'Готово. Тема «{LESSON_TITLE}»: блоков {blocks_n}, вопросов в тесте: {q_n}.'
        ))
