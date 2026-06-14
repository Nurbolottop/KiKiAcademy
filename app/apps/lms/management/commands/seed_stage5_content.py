"""Наполняет ЭТАП 5 — Поверхности курса «Обучение клинера» учебным контентом.

Темы: стекло, зеркало, ламинат, паркет, кафель, мрамор, мебель, кухонные
поверхности, техника, деликатные поверхности. Команда перезаписывает блоки
уроков ЭТАП 5 и пересобирает тест.

    python manage.py seed_stage5_content
    python manage.py seed_stage5_content --no-images   # только текст, без загрузки фото

Фото поверхностей подбираются автоматически из Wikimedia Commons (свободные
лицензии), скачиваются и сжимаются в WEBP (ResizedImageField).
"""
import json
import time
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Answer, Course, Lesson, LessonBlock, Question, Topic

COURSE_TITLE = 'Обучение клинера'
TOPIC_TITLE = 'ЭТАП 5 — Поверхности'
EXAMPLE_VIDEO = 'https://youtu.be/EXAMPLE'

UA = {'User-Agent': 'KIKIAcademyBot/1.0 (internal training; contact admin)'}
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'

# Поисковые запросы фото для каждой поверхности (Wikimedia Commons, англ.)
IMAGE_QUERIES = {
    'Стекло': 'window cleaning glass',
    'Зеркало': 'mirror wall room',
    'Ламинат': 'laminate flooring',
    'Паркет': 'parquet wood floor',
    'Кафель': 'ceramic tile bathroom wall',
    'Мрамор': 'marble floor surface',
    'Мебель': 'wooden furniture living room',
    'Кухонные поверхности': 'kitchen countertop worktop',
    'Техника': 'stainless steel kitchen appliances',
    'Деликатные поверхности': 'leather sofa armchair',
}


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


LESSONS = [
    ('Стекло', [
        ('text',
         '<h3>🪟 Стекло</h3>'
         '<p>Окна, стеклянные двери, столешницы, перегородки. Главная задача — '
         '<strong>чистота без разводов и ворса</strong>.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Средство для стекла + безворсовая микрофибра или сгон',
              'Сначала убрать грязь/пыль, затем полировать сухой салфеткой',
              'Движения сверху вниз, без пропусков',
              'Не мыть под прямым солнцем — сохнет и оставляет разводы')),
        ('text',
         warn('Абразив и жёсткие щётки <strong>царапают</strong> стекло. Присохшее снимаем '
              'специальным скребком под небольшим углом, смочив поверхность.')),
        ('image', 'Загрузите фото: вымытое стекло без разводов'),
    ]),
    ('Зеркало', [
        ('text',
         '<h3>🪞 Зеркало</h3>'
         '<p>Та же техника, что и стекло, но <strong>беречь заднюю кромку</strong> — влага по '
         'краям разрушает отражающий слой (появляются тёмные пятна).</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Средство для стекла — на салфетку, не лить на зеркало',
              'Безворсовая микрофибра, финиш — сухой полировкой',
              'Не допускать затёков средства за кромку и под раму',
              'В санузле — отдельная салфетка для стекла, не санузельная')),
        ('text',
         warn('Нельзя обильно мочить края и стыки зеркала — вода под слоем серебра '
              'оставляет чёрные пятна навсегда.')),
    ]),
    ('Ламинат', [
        ('text',
         '<h3>🟫 Ламинат</h3>'
         '<p>Ламинат <strong>боится воды</strong>: влага попадает в стыки, доски вздуваются. '
         'Моют <strong>хорошо отжатой</strong> насадкой, почти насухо.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Сначала пропылесосить/подмести песок (царапает)',
              'Швабра хорошо отжата — без луж',
              'Нейтральное средство для ламината, не агрессивное',
              'Двигаться вдоль досок',
              'Сразу убирать пролитую воду')),
        ('text',
         warn('<strong>Нельзя</strong>: мокрая швабра и лужи, абразивы, агрессивная химия, '
              'пар на стыки. Вода в швах = вздутие, замена пола.')),
        ('image', 'Загрузите фото: правильно вымытый ламинат'),
    ]),
    ('Паркет', [
        ('text',
         '<h3>🪵 Паркет</h3>'
         '<p>Натуральное дерево — деликатная и дорогая поверхность. Боится воды и абразива, '
         'требует <strong>специальных средств для паркета</strong>.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Пропылесосить/смести песок и пыль',
              'Слегка влажная мягкая насадка, специальное средство',
              'Двигаться вдоль волокон дерева',
              'Никаких луж — сразу вытирать насухо',
              'Защитные/полировочные средства — по типу покрытия (лак/масло)')),
        ('text',
         warn('Паркет нельзя заливать водой, тереть абразивом и мыть агрессивной химией. '
              'Сомневаешься в средстве — тест на незаметном участке и спроси менеджера.')),
    ]),
    ('Кафель', [
        ('text',
         '<h3>⬜ Кафель и плитка</h3>'
         '<p>Прочная поверхность санузла и кухни. Главная сложность — <strong>швы</strong> '
         '(затирка), где скапливается грязь, налёт и плесень.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Плитка — универсальное или кислотное средство от налёта',
              'Швы — щётка, при необходимости пар/спецсредство от плесени',
              'Глянцевую плитку — насухо до блеска, без разводов',
              'Сверху вниз, финиш — пол')),
        ('text',
         warn('Кислоту на плитке держим по инструкции и тщательно смываем. На натуральном камне '
              '(не керамика) кислоту <strong>не применяем</strong> — см. урок «Мрамор».')),
        ('image', 'Загрузите фото: чистая плитка и швы (до/после)'),
    ]),
    ('Мрамор', [
        ('text',
         '<h3>🏛️ Мрамор и натуральный камень</h3>'
         '<p>Мрамор, гранит, травертин, оникс — <strong>боятся кислоты</strong>. Кислота '
         'разъедает камень, оставляет матовые пятна (травление) навсегда.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Только <strong>нейтральные</strong> (pH 7) средства для камня',
              'Мягкая микрофибра, без абразива',
              'Пролитое (особенно кислое: сок, уксус) убирать сразу',
              'Полировка/защита — специальными средствами для камня')),
        ('text',
         warn('<strong>КАТЕГОРИЧЕСКИ нельзя</strong> на мраморе: кислотные средства, абразивы, '
              'универсальные средства для сантехники. Результат — испорченный камень и убыток.')),
        ('text',
         note('Если не уверены, камень это или керамика — относитесь как к камню: нейтральное '
              'средство и тест. Так безопаснее.')),
    ]),
    ('Мебель', [
        ('text',
         '<h3>🛋️ Мебель</h3>'
         '<p>Корпусная (дерево, ЛДСП, глянец) и мягкая (ткань, кожа). У каждой — свой подход, '
         'общий принцип — <strong>деликатность</strong>.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Корпусная: мягкая салфетка, средство на салфетку, не мочить стыки',
              'Глянец/лак: только мягкая микрофибра, без абразива',
              'Полироль для дерева — по необходимости',
              'Мягкая (ткань): пылесос/сухая чистка, химчистка по запросу',
              'Кожа: специальные мягкие средства, не мочить обильно')),
        ('text',
         warn('Абразивы и агрессивная химия портят лак, глянец и обивку. Вода в стыках ЛДСП '
              'вызывает разбухание. Деликатность — основа.')),
    ]),
    ('Кухонные поверхности', [
        ('text',
         '<h3>🍳 Кухонные поверхности</h3>'
         '<p>Столешницы, фартук, фасады, мойка. Главные враги — <strong>жир и нагар</strong>, '
         'работают щелочные обезжириватели. Но материал столешницы решает выбор средства.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Жир на плите/фартуке/вытяжке — щелочной обезжириватель',
              'Столешница из камня — нейтральное средство (не кислота/абразив)',
              'ЛДСП/пластик — универсальное мягкое средство, не заливать стыки',
              'Мойку и кран — после поверхностей',
              'Рабочую зону (где готовят) — чистой кухонной салфеткой')),
        ('text',
         warn('Каменную столешницу нельзя кислотой и абразивом (см. «Мрамор»). Нагар не трём '
              'металлом до царапин — даём средству растворить.')),
        ('image', 'Загрузите фото: чистая кухонная зона (до/после)'),
    ]),
    ('Техника', [
        ('text',
         '<h3>📺 Бытовая техника и электроника</h3>'
         '<p>Холодильник, плита, духовка, микроволновка, ТВ, экраны. Главное правило — '
         '<strong>средство на салфетку, не на технику</strong>, и беречь электронику от воды.</p>'),
        ('text',
         '<h3>🧭 Технология</h3>'
         + li('Снаружи — мягкая микрофибра, средство на салфетку',
              'Экраны (ТВ, панели) — сухая/чуть влажная мягкая салфетка, без спирта по полировке',
              'Нержавейку — спецсредство/полироль вдоль шлифовки, без разводов',
              'Жир на плите/духовке — обезжириватель с выдержкой',
              'Не лить воду на кнопки, разъёмы, щели')),
        ('text',
         warn('Вода и влага в электронике = поломка и удар током. Технику по возможности '
              'обесточить, не распылять средство прямо на панели и экраны.')),
    ]),
    ('Деликатные поверхности', [
        ('text',
         '<h3>💠 Деликатные поверхности</h3>'
         '<p>Натуральный камень, дерево, глянец, экраны, кожа, акрил, позолота, антиквариат. '
         'Общее правило — <strong>минимум воздействия и обязательный тест</strong>.</p>'),
        ('text',
         '<h3>🧭 Золотые правила</h3>'
         + li('Сначала <strong>тест на незаметном участке</strong>',
              'Нейтральное средство, мягкая микрофибра',
              'Средство — на салфетку, не на поверхность',
              'Без абразива, без агрессивной химии, без обильной воды',
              'Сомневаешься — не рискуй, спроси менеджера')),
        ('text',
         warn('Порча деликатной поверхности — это убыток и претензия. Лучше потратить минуту на '
              'уточнение, чем оплачивать дорогую вещь.')),
        ('text',
         ok('Принцип всей работы с поверхностями: <strong>знай материал → выбери средство → '
            'проверь → работай деликатно</strong>.')),
        ('video', (EXAMPLE_VIDEO, 'Загрузите видео: работа с деликатными поверхностями')),
    ]),
]

QUIZ = [
    ('Как правильно мыть стекло и зеркала?', [
        ('Безворсовой салфеткой, средство на салфетку, без прямого солнца', True),
        ('Абразивной губкой с напором воды', False),
        ('Обильно поливая, включая кромки зеркала', False),
    ]),
    ('Почему ламинат моют хорошо отжатой шваброй?', [
        ('Вода в стыках вызывает вздутие досок', True),
        ('Чтобы быстрее сохло, разницы нет', False),
        ('Ламинат любит много воды', False),
    ]),
    ('Какое средство НЕЛЬЗЯ применять на мраморе?', [
        ('Кислотное', True),
        ('Нейтральное (pH 7)', False),
        ('Специальное для камня', False),
    ]),
    ('Чем убирают жир на кухонной плите и фартуке?', [
        ('Щелочным обезжиривателем', True),
        ('Кислотой для сантехники', False),
        ('Средством для стекла', False),
    ]),
    ('Как наносить средство на технику и экраны?', [
        ('На салфетку, а не на саму технику', True),
        ('Распылять прямо на экран и кнопки', False),
        ('Заливать водой', False),
    ]),
    ('Что обязательно перед уборкой деликатной поверхности?', [
        ('Тест средства на незаметном участке', True),
        ('Сразу тереть абразивом', False),
        ('Залить водой', False),
    ]),
    ('Как мыть паркет?', [
        ('Слегка влажной насадкой, спецсредством, вдоль волокон', True),
        ('Мокрой шваброй с агрессивной химией', False),
        ('Жёсткой щёткой и абразивом', False),
    ]),
    ('Если не уверены — камень это или керамика, как поступить?', [
        ('Относиться как к камню: нейтральное средство и тест', True),
        ('Применить кислоту для надёжности', False),
        ('Тереть абразивом', False),
    ]),
]


def _get(url, timeout, retries=4):
    """GET с повторами и бэкоффом (Wikimedia режет частые запросы — 429)."""
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def fetch_commons_image(query, timeout=60):
    """Ищет фото на Wikimedia Commons и возвращает (bytes, source_url) или (None, None)."""
    params = urllib.parse.urlencode({
        'action': 'query', 'generator': 'search',
        'gsrsearch': f'filetype:bitmap {query}',
        'gsrnamespace': '6', 'gsrlimit': '8',
        'prop': 'imageinfo', 'iiprop': 'url|mime', 'iiurlwidth': '1400',
        'format': 'json',
    })
    raw = _get(f'{COMMONS_API}?{params}', timeout)
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
    except Exception:
        return None, None
    pages = (data.get('query') or {}).get('pages') or {}
    items = sorted(pages.values(), key=lambda p: p.get('index', 999))
    for p in items:
        info = (p.get('imageinfo') or [{}])[0]
        mime = info.get('mime', '')
        url = info.get('thumburl') or info.get('url')
        if not url or not mime.startswith('image/') or 'svg' in mime:
            continue
        img = _get(url, timeout)
        if img and len(img) > 5000:  # отсекаем заглушки/ошибки
            return img, info.get('descriptionurl') or url
    return None, None


class Command(BaseCommand):
    help = 'Наполняет ЭТАП 5 — Поверхности учебным контентом, фото и тестом.'

    def add_arguments(self, parser):
        parser.add_argument('--no-images', action='store_true',
                            help='Не скачивать фото, только текст.')

    @transaction.atomic
    def handle(self, *args, **options):
        no_images = options['no_images']
        course = Course.objects.filter(title=COURSE_TITLE).first()
        if not course:
            self.stdout.write(self.style.WARNING(f'Курс «{COURSE_TITLE}» не найден.'))
            return
        topic = Topic.objects.filter(course=course, title=TOPIC_TITLE).first()
        if not topic:
            self.stdout.write(self.style.WARNING(f'Этап «{TOPIC_TITLE}» не найден.'))
            return

        blocks_n = img_ok = img_fail = 0
        for order, (title, items) in enumerate(LESSONS, start=1):
            lesson = Lesson.objects.filter(topic=topic, title=title).first()
            if not lesson:
                self.stdout.write(self.style.WARNING(f'  Урок не найден: {title}'))
                continue
            lesson.order = order
            lesson.save(update_fields=['order'])
            lesson.blocks.all().delete()
            last_order = 0
            for b_order, (kind, payload) in enumerate(items, start=1):
                if kind == 'text':
                    LessonBlock.objects.create(lesson=lesson, kind=LessonBlock.Kind.TEXT,
                                               order=b_order, text=payload)
                elif kind == 'image':
                    LessonBlock.objects.create(lesson=lesson, kind=LessonBlock.Kind.IMAGE,
                                               order=b_order, caption=payload)
                elif kind == 'video':
                    url, caption = payload
                    LessonBlock.objects.create(lesson=lesson, kind=LessonBlock.Kind.VIDEO,
                                               order=b_order, video_url=url, caption=caption)
                blocks_n += 1
                last_order = b_order

            # Фото поверхности из Wikimedia Commons
            query = IMAGE_QUERIES.get(title)
            if query and not no_images:
                time.sleep(1.5)  # пауза, чтобы Wikimedia не резал частые запросы
                img, src = fetch_commons_image(query)
                if img:
                    # Заполняем первый пустой фото-блок, иначе добавляем новый в конец.
                    block = lesson.blocks.filter(
                        kind=LessonBlock.Kind.IMAGE, image='').order_by('order').first()
                    if not block:
                        last_order += 1
                        block = LessonBlock.objects.create(
                            lesson=lesson, kind=LessonBlock.Kind.IMAGE, order=last_order)
                        blocks_n += 1
                    if not block.caption:
                        block.caption = f'{title} · фото: Wikimedia Commons'
                    else:
                        block.caption = f'{block.caption} · фото: Wikimedia Commons'
                    block.image.save(f'surface-{order}.jpg', ContentFile(img), save=True)
                    img_ok += 1
                    self.stdout.write(f'    🖼  {title}: фото загружено')
                else:
                    img_fail += 1
                    self.stdout.write(self.style.WARNING(f'    ! {title}: фото не найдено'))

            self.stdout.write(f'  ✓ {title} ({len(items)} блоков)')

        quiz = Lesson.objects.filter(topic=topic, title='Тест', kind=Lesson.Kind.QUIZ).first()
        q_n = 0
        if quiz:
            quiz.order = len(LESSONS) + 1
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
            f'Готово. Блоков: {blocks_n}, фото: {img_ok} загружено / {img_fail} не найдено, '
            f'вопросов в тесте: {q_n}.'
        ))
