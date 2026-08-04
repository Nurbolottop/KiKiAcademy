"""Добавляет услугу «Мойка фасадов» в курс «Обучение клинера» (ЭТАП 6 — Услуги).

Только ДОБАВЛЯЕТ новый урок и его блоки. Существующие уроки/блоки не удаляет.
Ставит урок перед «Тестом» (единственная правка существующего — порядок теста).
Идемпотентна.

    python manage.py seed_cleaner_facade
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, Lesson, LessonBlock

COURSE_ID = 1
TOPIC_MATCH = 'Услуги'
LESSON_TITLE = 'Мойка фасадов'


def h(t):
    return f'<h3>{t}</h3>'


def p(*xs):
    return ''.join(f'<p>{x}</p>' for x in xs)


def li(*xs):
    return '<ul>' + ''.join(f'<li>{x}</li>' for x in xs) + '</ul>'


def ol(*xs):
    return '<ol>' + ''.join(f'<li>{x}</li>' for x in xs) + '</ol>'


def _c(html, color, icon):
    return (f'<div style="background:{color}1f;border-left:4px solid {color};'
            f'padding:12px 16px;border-radius:10px;margin:14px 0;">{icon} ' + html + '</div>')


def note(x):
    return _c(x, '#6c63ff', 'ℹ️')


def ok(x):
    return _c(x, '#22c55e', '✅')


def warn(x):
    return _c(x, '#ef4444', '⚠️')


BLOCKS = [
    ('text', h('📋 Описание')
     + p('<strong>Дополнительная услуга.</strong> Мойка фасадов — это очистка внешней '
         'поверхности здания: фасадного остекления, витрин, входных групп и облицовочных панелей. '
         'Чаще всего заказывают владельцы коммерческих помещений, магазинов, офисов, кафе, а также '
         'жильцы домов с панорамным остеклением и балконами.',
         'Может выполняться как отдельная услуга или входить в комплексную уборку объекта '
         '(например, вместе с мойкой панорамных окон).')),

    ('text', h('🏢 Что относится к фасаду')
     + p('Фасад — это не только стекло. Моем всю внешнюю поверхность, которую заказал клиент:')
     + li('<strong>Фасадное остекление</strong> — стеклянные стены, витражи, панорамные окна '
          'снаружи',
          '<strong>Витрины</strong> магазинов и входные группы',
          '<strong>Облицовочные панели</strong> (алюкобонд, композит, керамогранит, металл)',
          '<strong>Козырьки, отливы, рамы и стыки</strong>',
          '<strong>Двери и стеклянные ограждения</strong> балконов и террас')),

    ('text', warn('<strong>Безопасность — на первом месте.</strong> Мойка фасада выше первого '
                  'этажа — это <strong>высотные работы</strong>. К ним допускаются только '
                  'обученные сотрудники со средствами страховки. Клинер <strong>никогда не '
                  'выполняет высотные работы самостоятельно и без согласования с менеджером</strong>. '
                  'При работе с земли/стремянки — устойчивое основание, сухая обувь, ограждение '
                  'зоны под фасадом.')),

    ('text', h('📦 Что входит в услугу')
     + li('Очистка фасадного остекления и витрин снаружи',
          'Мойка облицовочных панелей и входных групп',
          'Удаление пыли, грязи, подтёков, следов дождя и налёта',
          'Очистка рам, стыков и отливов',
          'Удаление наклеек, скотча, следов клея (по договорённости)',
          'Финальная протирка стекла без разводов')),

    ('text', h('🧴 Инвентарь и средства')
     + li('Телескопическая штанга со щёткой и подачей воды',
          'Осмотическая (деминерализованная) вода — сохнет <strong>без разводов</strong>',
          'Стекломой, склизг (сгон) и профессиональная химия для стекла',
          'Мягкие безворсовые салфетки и микрофибра',
          'Скребок с лезвием — только для стекла и только для сильных загрязнений',
          'Страховочное снаряжение и СИЗ для высотных работ (при необходимости)')),

    ('text', h('🧽 Технология и порядок')
     + ol('Оценить фасад: материал, высота, тип загрязнений, нужен ли допуск на высоту',
          'Оградить зону внизу, предупредить о работах',
          'Убрать сухую пыль и песок сверху, чтобы не тереть абразивом по стеклу/панели',
          'Мыть <strong>сверху вниз</strong> — грязная вода стекает на ещё не вымытое',
          'Наносить средство, обрабатывать щёткой, смывать чистой (осмотической) водой',
          'Стекло досушивать сгоном без разводов, панели — не тереть абразивом',
          'Проверить результат снизу и под разными углами света')),

    ('text', ok('Простыми словами: моем сверху вниз, чистой водой и без абразива, а стекло '
                'досушиваем сгоном — тогда фасад блестит и без разводов.')),

    ('text', h('✅ Как проверить качество')
     + li('Посмотреть на стекло с разных точек и на свет — нет разводов, подтёков и ворсинок',
          'Панели — равномерно чистые, без пятен и царапин',
          'Рамы, стыки и отливы — без грязи и потёков',
          'Зона под фасадом убрана, вода не оставила луж и следов')),

    ('text', warn('<strong>Частые ошибки:</strong> мыть обычной водопроводной водой (остаются '
                  'известковые разводы) · тереть панели абразивом (царапины) · мыть снизу вверх · '
                  'работать на высоте без допуска и страховки · оставлять следы клея и наклеек.')),

    ('video', '🎥 Видео: техника мойки фасада без разводов'),
    ('image', 'Мойка фасадов — что моем'),
    ('image', 'Мойка фасадов — порядок работ сверху вниз'),
]


class Command(BaseCommand):
    help = 'Добавляет услугу «Мойка фасадов» в курс клинера (только добавление).'

    @transaction.atomic
    def command_body(self):
        course = Course.objects.get(id=COURSE_ID)
        topic = course.topics.filter(title__icontains=TOPIC_MATCH).first()
        if topic is None:
            self.stderr.write(self.style.ERROR('Тема услуг не найдена.'))
            return

        lesson = topic.lessons.filter(title=LESSON_TITLE).first()
        created = False
        if lesson is None:
            # Ставим перед первым тестом: сдвигаем тесты на +1.
            quizzes = list(topic.lessons.filter(kind=Lesson.Kind.QUIZ).order_by('order', 'id'))
            if quizzes:
                new_order = quizzes[0].order
                for qz in quizzes:
                    qz.order += 1
                    qz.save(update_fields=['order'])
            else:
                new_order = (max([l.order for l in topic.lessons.all()], default=0) + 1)
            lesson = Lesson.objects.create(
                topic=topic, title=LESSON_TITLE, order=new_order,
                kind=Lesson.Kind.CONTENT, is_published=True,
            )
            created = True

        existing_txt = set(b.text for b in lesson.blocks.all())
        existing_cap = set(b.caption for b in lesson.blocks.all())
        mo = max([b.order for b in lesson.blocks.all()], default=0)
        added = 0
        for kind, val in BLOCKS:
            if kind == 'text':
                if val in existing_txt:
                    continue
                mo += 1
                LessonBlock.objects.create(lesson=lesson, kind='TEXT', order=mo, text=val)
                existing_txt.add(val)
                added += 1
            elif kind == 'image':
                if val in existing_cap:
                    continue
                mo += 1
                LessonBlock.objects.create(lesson=lesson, kind='IMAGE', order=mo, caption=val)
                existing_cap.add(val)
                added += 1
            elif kind == 'video':
                if val in existing_cap:
                    continue
                mo += 1
                LessonBlock.objects.create(lesson=lesson, kind='VIDEO', order=mo,
                                           caption=val, video_url='')
                existing_cap.add(val)
                added += 1

        self.stdout.write(self.style.SUCCESS(
            f'Урок «{LESSON_TITLE}»: {"создан" if created else "уже был"}. '
            f'Добавлено блоков: {added}.'))

    def handle(self, *args, **options):
        self.command_body()
