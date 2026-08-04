"""Добавляет карточку инвентаря «Химчистка-аппарат (Робоклин)» в курс клинера
(ЭТАП 3 — Инвентарь).

Только ДОБАВЛЯЕТ новый урок и его блоки. Существующее не удаляет.
Ставит перед «Тестом» (единственная правка существующего — порядок теста).
Идемпотентна.

    python manage.py seed_cleaner_roboclean
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, Lesson, LessonBlock

COURSE_ID = 1
TOPIC_MATCH = 'Инвентар'
LESSON_TITLE = 'Химчистка-аппарат (Робоклин)'


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
    ('text', h('💧 Что это')
     + p('<strong>Робоклин</strong> — моющий аппарат с <strong>аквафильтром</strong> для '
         '<strong>химчистки</strong> мягкой мебели, матрасов и ковров. Он распыляет моющий '
         'раствор на поверхность и тут же <strong>всасывает грязь вместе с влагой</strong> '
         '(экстракция) — так из ткани вытягивается пыль, пятна, клещи и запахи.',
         'За счёт водяного фильтра аппарат используют и для <strong>влажной уборки/сбора '
         'пыли</strong> с чистым выхлопом воздуха.')),

    ('image', 'Химчистка-аппарат (Робоклин) — общий вид'),

    ('text', h('🔧 Как пользоваться')
     + ol('Залить <strong>чистую воду</strong> в бак и добавить профессиональное средство для '
          'химчистки в нужной пропорции',
          'Собрать насадку и шланг, проверить, что баки закрыты плотно',
          'Распылить раствор на участок ткани (не переувлажняя)',
          'Сразу пройти <strong>экстрактором</strong>, всасывая раствор вместе с грязью',
          'Идти внахлёст, полосами, до чистой всасываемой воды',
          'Дать изделию просохнуть (проветрить помещение)')),

    ('text', h('📍 Где применяется')
     + li('Диваны, кресла, стулья с тканевой обивкой',
          'Матрасы',
          'Ковры и ковровые покрытия',
          'Мягкие изголовья кроватей',
          'Автомобильные сиденья (по договорённости)',
          'Сбор пыли и влаги через аквафильтр при влажной уборке')),

    ('text', warn('<strong>Правила и безопасность:</strong> не всасывать крупный мусор, стекло и '
                  'острые предметы · <strong>не переувлажнять</strong> ткань и матрас (иначе '
                  'долго сохнет и появляется плесень/запах) · беречь корпус и розетку от воды · '
                  'проверять провод перед работой · тест средства на незаметном участке.')),

    ('text', h('🧼 Уход за аппаратом')
     + li('После работы <strong>слить оба бака</strong> (чистый и грязный)',
          'Промыть аквафильтр, бак и насадки, всё просушить',
          'Не оставлять воду внутри — иначе запах и плесень',
          'Промывать/чистить фильтр по инструкции',
          'Хранить сухим, шланг не заламывать')),

    ('text', ok('Простыми словами: залил воду со средством → распылил → сразу высосал грязь. '
                'Главное — не заливать слишком мокро и после работы всё промыть и просушить.')),

    ('video', '🎥 Видео: химчистка дивана аппаратом Робоклин'),
    ('image', 'Робоклин — экстракция обивки дивана'),
]


class Command(BaseCommand):
    help = 'Добавляет карточку «Химчистка-аппарат (Робоклин)» в инвентарь клинера.'

    @transaction.atomic
    def command_body(self):
        course = Course.objects.get(id=COURSE_ID)
        topic = course.topics.filter(title__icontains=TOPIC_MATCH).first()
        if topic is None:
            self.stderr.write(self.style.ERROR('Тема инвентаря не найдена.'))
            return

        lesson = topic.lessons.filter(title=LESSON_TITLE).first()
        created = False
        if lesson is None:
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
                if val in existing_cap and val != '':
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
