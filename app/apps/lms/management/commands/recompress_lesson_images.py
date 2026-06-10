"""Пересжимает уже загруженные фото уроков в WEBP (макс. 1600px, качество 82)
и удаляет исходные несжатые файлы.

    python manage.py recompress_lesson_images
"""
import os
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from apps.lms.models import LessonBlock

MAX_SIZE = 1600
QUALITY = 82


class Command(BaseCommand):
    help = 'Пересжимает существующие фото уроков в WEBP (макс. 1600px) и удаляет оригиналы.'

    def handle(self, *args, **options):
        qs = LessonBlock.objects.exclude(image='').exclude(image__isnull=True)
        done = skipped = failed = 0

        for block in qs:
            if not block.image:
                continue
            old_name = block.image.name
            if old_name.lower().endswith('.webp'):
                skipped += 1
                continue
            try:
                block.image.open('rb')
                img = Image.open(block.image)
                img = img.convert('RGB')
                img.thumbnail((MAX_SIZE, MAX_SIZE))
                buf = BytesIO()
                img.save(buf, format='WEBP', quality=QUALITY)
                block.image.close()
                buf.seek(0)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                self.stdout.write(self.style.WARNING(f'  ! {old_name}: {exc}'))
                continue

            storage = block.image.storage
            base = os.path.splitext(os.path.basename(old_name))[0]
            # Сохраняем новый WEBP (save=True перезапишет поле); затем удаляем старый файл.
            block.image.save(f'{base}.webp', ContentFile(buf.read()), save=True)
            try:
                if storage.exists(old_name):
                    storage.delete(old_name)
            except Exception:  # noqa: BLE001
                pass
            done += 1
            self.stdout.write(f'  ✓ {old_name} -> {block.image.name}')

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Сжато: {done}, пропущено (уже webp): {skipped}, ошибок: {failed}.'
        ))
