import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lms', '0013_alter_lessonblock_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score_pct', models.PositiveIntegerField(default=0, verbose_name='Результат, %')),
                ('correct_count', models.PositiveIntegerField(default=0, verbose_name='Верных ответов')),
                ('total_count', models.PositiveIntegerField(default=0, verbose_name='Всего вопросов')),
                ('passed', models.BooleanField(default=False, verbose_name='Пройден')),
                ('detail', models.JSONField(blank=True, default=list, verbose_name='Разбор ответов')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата попытки')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to='lms.lesson', verbose_name='Тест')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Попытка теста',
                'verbose_name_plural': 'История тестов',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(fields=['user', 'lesson', '-created_at'], name='lms_quizatt_user_id_3d6f1a_idx'),
        ),
    ]
