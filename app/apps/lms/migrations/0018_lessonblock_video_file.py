import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0017_add_ky_translation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonblock',
            name='video_file',
            field=models.FileField(
                blank=True, null=True, upload_to='lessons/videos/',
                validators=[django.core.validators.FileExtensionValidator(['mp4', 'webm', 'mov', 'm4v'])],
                verbose_name='Видеофайл (mp4 / webm)',
            ),
        ),
    ]
