"""Восстанавливает привязку загруженных фото услуг (ЭТАП 6 клинера).

Фото отвязались при повторных прогонах seed_stage6. Файлы целы в media —
команда возвращает их в нужные уроки с правильными подписями. Идемпотентна:
не плодит дубли (сверяет по имени файла).

    python manage.py relink_service_photos
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lms.models import Course, LessonBlock, Topic

COURSE_TITLE = 'Обучение клинера'
TOPIC_TITLE = 'ЭТАП 6 — Услуги'
DIR = 'lessons/images'

# Урок → [(файл, подпись), ...] в нужном порядке
MAPPING = {
    'Влажная уборка/поддерживающая уборка': [
        ('вл.webp', 'Влажная уборка — комната'),
        ('f0ae26cf-94e4-41e6-8039-55266b4d382e.webp', 'Влажная уборка — кухня'),
        ('вл3.webp', 'Влажная уборка — ванная и туалет'),
    ],
    'Генеральная уборка/Стандарт/Премиум/Вип': [
        ('06abe96b-c170-4586-a214-8aeb0f5d78a6.webp', 'Генеральная Стандарт — комната'),
        ('5395e429-9ef0-4fc5-b1e2-f479c61a48be.webp', 'Генеральная Стандарт — кухня'),
        ('cd480d8f-e4ed-4e47-baba-b4ae5920d560.webp', 'Генеральная Стандарт — санузел'),
        ('1.webp', 'Генеральная Премиум — комната'),
        ('db9eb3ce-b139-4469-9177-4a54ad9f1b97.webp', 'Генеральная Премиум — кухня'),
        ('d72d505f-03ee-431a-a712-73bd89764da1.webp', 'Генеральная Премиум — санузел'),
        ('6ab92543-0526-44bf-831e-cd6f4a36e31d.webp', 'Генеральная VIP — комната'),
        ('ed06f8df-7b42-46e4-a0b8-48f5bb97d96f.webp', 'Генеральная VIP — кухня'),
        ('f22bc1a2-528e-44ba-9544-8350a36248f5.webp', 'Генеральная VIP — санузел'),
        ('8d1e0218-91d6-4fea-bf4c-37af505468cd.webp', 'Генеральная уборка — до / после'),
    ],
    'После ремонта': [
        ('ChatGPT_Image_14_июн._2026_г._14_51_16.webp', 'После ремонта — комната'),
        ('a3cdb6d9-5bac-4634-b5aa-0fc4f657f143.webp', 'После ремонта — кухня'),
        ('5736ef88-01db-4c28-8df4-33de334fe596.webp', 'После ремонта — санузел'),
    ],
    'Мытье окон': [
        ('е.webp', 'Мытьё окон — что моем'),
        ('37b777ce-2c4f-4038-b170-1ee3a6c509f6.webp', 'Мытьё окон — порядок работ'),
    ],
    'Химчистка мебели': [
        ('0d21c955-5306-4362-a2f1-1ee20b3466b5.webp', 'Химчистка мебели — до / после'),
        ('785cdb50-a07c-43ae-b566-a89c9496b884.webp', 'Химчистка мебели — что чистим'),
        ('a22395a1-99e9-456e-99f4-c13863db7ae5.webp', 'Химчистка мебели — как чистим'),
    ],
}


class Command(BaseCommand):
    help = 'Возвращает загруженные фото услуг (ЭТАП 6 клинера) в уроки.'

    @transaction.atomic
    def handle(self, *args, **options):
        course = Course.objects.filter(title=COURSE_TITLE).first()
        topic = Topic.objects.filter(course=course, title=TOPIC_TITLE).first() if course else None
        if not topic:
            self.stdout.write(self.style.WARNING('Курс/этап не найден.'))
            return

        linked = skipped = missing = 0
        for lesson in topic.lessons.all():
            pairs = MAPPING.get(lesson.title)
            if not pairs:
                continue
            # Уже привязанные файлы в этом уроке — чтобы не дублировать.
            existing = {
                os.path.basename(b.image.name)
                for b in lesson.blocks.filter(kind=LessonBlock.Kind.IMAGE)
                if b.image and b.image.name
            }
            # Удаляем пустые фото-плейсхолдеры (без файла).
            lesson.blocks.filter(kind=LessonBlock.Kind.IMAGE, image='').delete()

            next_order = (lesson.blocks.order_by('-order').first().order + 1
                          if lesson.blocks.exists() else 1)
            for fname, caption in pairs:
                if fname in existing:
                    skipped += 1
                    continue
                path = os.path.join(settings.MEDIA_ROOT, DIR, fname)
                if not os.path.exists(path):
                    missing += 1
                    self.stdout.write(self.style.WARNING(f'  ! нет файла: {fname}'))
                    continue
                blk = LessonBlock(lesson=lesson, kind=LessonBlock.Kind.IMAGE,
                                  order=next_order, caption=caption)
                blk.image.name = f'{DIR}/{fname}'
                blk.save()
                next_order += 1
                linked += 1
            self.stdout.write(f'  ✓ {lesson.title}: +{len([p for p in pairs])} фото')

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Привязано: {linked}, пропущено (уже было): {skipped}, нет файла: {missing}.'
        ))
