"""Логичная перестройка курса «Обучение СММ / Мобилографа» (id 15).

- Перенумеровывает существующие этапы в сплошной порядок 1..9 (убирает дыры
  1,2,3,5,6,8,11) — меняются только title/order тем, контент не трогается.
- Добавляет два недостающих этапа с подробным контентом:
  «Тексты, сценарии и хуки» и «Монтаж и обработка».
Ничего НЕ удаляет. Идемпотентна.

    python manage.py seed_smm_restructure
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, Lesson, LessonBlock, Topic

COURSE_ID = 15


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


def q(x):
    return _c(x, '#22c55e', '💬')


def vid(caption):
    return ('video', caption)


def img(caption):
    return ('image', caption)


# Переименование/перенумерация существующих тем: topic_id -> (новый заголовок, порядок)
RETITLE = {
    51: ('ЭТАП 1 — Введение', 1),
    52: ('ЭТАП 2 — Контент', 2),
    53: ('ЭТАП 4 — Съёмка', 4),
    55: ('ЭТАП 6 — Социальные сети', 6),
    56: ('ЭТАП 7 — Маркетинг', 7),
    58: ('ЭТАП 8 — Работа с CRM', 8),
    61: ('ЭТАП 9 — Финальная аттестация', 9),
}

# Новые этапы: (заголовок, порядок, [ (урок, [html-блоки]) ])
NEW_TOPICS = [
    ('ЭТАП 3 — Тексты, сценарии и хуки', 3, [
        ('Сценарий ролика', [
            h('🎬 Зачем нужен сценарий')
            + p('Даже короткий Reels снимается по сценарию. Сценарий — это план: что показать, в '
                'каком порядке и что сказать. Без него ролик получается затянутым и «ни о чём», а '
                'зритель уходит.')
            + h('Структура продающего ролика')
            + ol('<strong>Хук</strong> (1–2 сек) — зацепка, ради которой досмотрят',
                 '<strong>Суть/трансформация</strong> — процесс, «до/после», польза',
                 '<strong>Результат</strong> — чистый эффект, эмоция',
                 '<strong>Призыв</strong> — «запишись», «ссылка в шапке»')
            + note('Сначала придумываем идею и хук, потом снимаем — а не наоборот.'),
            h('🗒️ Раскадровка')
            + p('Перед съёмкой полезно набросать кадры списком: какие планы нужны (общий, средний, '
                'макро), сколько секунд каждый, что в кадре. Так на съёмке ничего не забудешь.')
            + li('Каждый кадр — 1–3 секунды',
                 'Снимаем с запасом и под разные ракурсы',
                 'Отмечаем, где будет текст/субтитр'),
            vid('🎥 Видео: разбор сценария удачного Reels'),
        ]),
        ('Хуки и первые секунды', [
            h('🪝 Что такое хук')
            + p('Хук — это первые 1–2 секунды, которые решают, досмотрит зритель или пролистает. '
                'Слабый хук = мало просмотров, каким бы хорошим ни был остальной ролик.')
            + h('Рабочие хуки для клининга')
            + li('Резкий контраст «до/после» сразу в кадре',
                 'Вопрос-боль: «Не успеваете убирать?»',
                 'Интрига: «Смотрите, что было под диваном…»',
                 'Эффектный момент: пар, блеск, вода стекает с окна',
                 'Цифра/факт: «Убрали квартиру за 3 часа»')
            + q('Первый кадр — самый сочный. Не начинай с логотипа и долгого вступления.'),
            ok('Простыми словами: покажи в первые секунды самое интересное — тогда досмотрят до '
               'конца.'),
        ]),
        ('Тексты к постам и подписи', [
            h('✍️ Подпись к посту/ролику')
            + p('Текст усиливает видео: объясняет пользу и ведёт к заявке. Пишем просто, на языке '
                'клиента, без канцелярита.')
            + h('Формула подписи')
            + ol('Цепляющая первая строка (её видно до «ещё»)',
                 'Польза/суть в 1–2 предложениях',
                 'Чёткий призыв к действию',
                 'Хэштеги по теме и городу')
            + li('Пиши короткими абзацами, добавляй эмодзи в меру',
                 'Один пост — одна мысль и один призыв'),
            note('Призыв должен быть конкретным: «Пишите в Direct слово «уборка» — рассчитаем '
                 'стоимость».'),
        ]),
    ]),
    ('ЭТАП 5 — Монтаж и обработка', 5, [
        ('Монтаж в CapCut', [
            h('✂️ Основы монтажа')
            + p('Монтаж превращает набор кадров в динамичный ролик. Для мобилографа основной '
                'инструмент — <strong>CapCut</strong> (бесплатный, на телефоне).')
            + h('Базовый порядок работы')
            + ol('Загрузить отснятый материал, отобрать лучшие дубли',
                 'Собрать ролик по сценарию: хук → суть → результат → призыв',
                 'Нарезать длинные куски, убрать паузы и «мусор»',
                 'Сделать склейки короткими и динамичными',
                 'Выровнять ритм под музыку')
            + li('Сцена 1–3 секунды, частая смена планов держит внимание',
                 'Убираем всё лишнее — ролик должен быть плотным'),
            vid('🎥 Видео: монтаж Reels в CapCut с нуля'),
        ]),
        ('Музыка, звук и субтитры', [
            h('🎵 Музыка и звук')
            + li('Берём <strong>трендовые звуки</strong> площадки — это повышает охват',
                 'Склейки делаем «на бит» музыки',
                 'Баланс громкости: музыка не должна забивать речь',
                 'Следим за авторскими правами (используем встроенную библиотеку)'),
            h('💬 Субтитры и текст на экране')
            + p('Большинство смотрит без звука, поэтому субтитры обязательны.')
            + li('Включаем авто-субтитры и проверяем ошибки',
                 'Крупный читаемый шрифт, контраст с фоном',
                 'Ключевые мысли дублируем текстом на экране'),
            ok('Простыми словами: тренд-звук + субтитры = больше охват и досмотры.'),
        ]),
        ('Переходы, эффекты и цвет', [
            h('🎚️ Переходы и скорость')
            + li('Простые переходы (склейка, приближение) работают лучше «пёстрых»',
                 'Ускорение/замедление — для процесса уборки и эффектных моментов',
                 'Не перегружать эффектами: они не должны отвлекать от сути'),
            h('🌈 Цвет и картинка')
            + li('Лёгкая цветокоррекция: чуть яркости, контраста, чёткости',
                 'Единый стиль обработки во всех роликах (узнаваемость бренда)',
                 'Не «пережигать» цвета — чистота должна выглядеть естественно'),
            warn('Частая ошибка новичка — гора переходов и эффектов. Меньше значит лучше: главное '
                 '— результат уборки в кадре.'),
        ]),
        ('Экспорт и публикация', [
            h('📤 Настройки экспорта')
            + li('Формат <strong>вертикальный 9:16</strong>, разрешение 1080p и выше',
                 'Частота 30–60 fps',
                 'Сохранять <strong>без водяных знаков</strong> (убрать вотермарку CapCut)',
                 'Проверить итог на телефоне перед публикацией'),
            h('🗓️ Публикация')
            + li('Выкладываем по контент-плану, в активное время аудитории',
                 'Один ролик — на все площадки (Reels, TikTok, Shorts)',
                 'Добавляем цепляющую подпись, призыв и хэштеги'),
            note('Держи исходники и финальные версии — пригодятся для повторного монтажа и отчётов.'),
        ]),
    ]),
]


class Command(BaseCommand):
    help = 'Логичная перестройка курса СММ: перенумерация этапов + 2 новых этапа.'

    @transaction.atomic
    def command_body(self):
        course = Course.objects.get(id=COURSE_ID)

        # 1) Перенумерация/переименование существующих тем.
        for tid, (title, order) in RETITLE.items():
            t = Topic.objects.filter(id=tid, course=course).first()
            if t:
                t.title = title
                t.order = order
                t.save(update_fields=['title', 'order'])

        # 2) Новые этапы с контентом.
        n_topics = n_lessons = n_blocks = 0
        for topic_title, order, lessons in NEW_TOPICS:
            topic, _ = Topic.objects.get_or_create(
                course=course, title=topic_title, defaults={'order': order})
            topic.order = order
            topic.save(update_fields=['order'])
            n_topics += 1

            for l_order, (lesson_title, blocks) in enumerate(lessons, start=1):
                lesson = topic.lessons.filter(title=lesson_title).first()
                if lesson is None:
                    lesson = Lesson.objects.create(
                        topic=topic, title=lesson_title, order=l_order,
                        kind=Lesson.Kind.CONTENT, is_published=True)
                    n_lessons += 1
                existing_txt = set(b.text for b in lesson.blocks.all())
                existing_cap = set(b.caption for b in lesson.blocks.all())
                mo = max([b.order for b in lesson.blocks.all()], default=0)
                for item in blocks:
                    kind, val = ('text', item) if isinstance(item, str) else item
                    if kind == 'text':
                        if val in existing_txt:
                            continue
                        mo += 1
                        LessonBlock.objects.create(lesson=lesson, kind='TEXT', order=mo, text=val)
                        existing_txt.add(val)
                        n_blocks += 1
                    elif kind == 'video':
                        if val in existing_cap:
                            continue
                        mo += 1
                        LessonBlock.objects.create(lesson=lesson, kind='VIDEO', order=mo,
                                                   caption=val, video_url='')
                        existing_cap.add(val)
                        n_blocks += 1
                    elif kind == 'image':
                        if val in existing_cap:
                            continue
                        mo += 1
                        LessonBlock.objects.create(lesson=lesson, kind='IMAGE', order=mo,
                                                   caption=val)
                        existing_cap.add(val)
                        n_blocks += 1

            # Тест в конец нового этапа.
            if not topic.lessons.filter(kind=Lesson.Kind.QUIZ).exists():
                Lesson.objects.create(topic=topic, title='Тест', order=99,
                                      kind=Lesson.Kind.QUIZ, is_published=True)

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Перенумеровано тем: {len(RETITLE)}. '
            f'Новых этапов: {n_topics}, уроков: {n_lessons}, блоков: {n_blocks}.'))
        for t in course.topics.all().order_by('order', 'id'):
            self.stdout.write(f'  [{t.order}] {t.title}')

    def handle(self, *args, **options):
        self.command_body()
