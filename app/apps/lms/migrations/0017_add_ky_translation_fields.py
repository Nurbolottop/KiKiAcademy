from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0016_role_smm_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='course', name='title_ky',
            field=models.CharField(blank=True, default='', max_length=200,
                                   verbose_name='Название (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='course', name='description_ky',
            field=models.TextField(blank=True, default='',
                                   verbose_name='Описание (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='topic', name='title_ky',
            field=models.CharField(blank=True, default='', max_length=200,
                                   verbose_name='Название (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lesson', name='title_ky',
            field=models.CharField(blank=True, default='', max_length=200,
                                   verbose_name='Название (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lesson', name='description_ky',
            field=models.TextField(blank=True, default='',
                                   verbose_name='Описание / введение (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lessonblock', name='text_ky',
            field=models.TextField(blank=True, default='',
                                   verbose_name='Текст (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lessonblock', name='caption_ky',
            field=models.CharField(blank=True, default='', max_length=255,
                                   verbose_name='Подпись (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='question', name='text_ky',
            field=models.TextField(blank=True, default='',
                                   verbose_name='Текст вопроса (кыргызча)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='answer', name='text_ky',
            field=models.CharField(blank=True, default='', max_length=500,
                                   verbose_name='Текст ответа (кыргызча)'),
            preserve_default=False,
        ),
    ]
