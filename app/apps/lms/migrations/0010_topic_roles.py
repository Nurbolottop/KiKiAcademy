from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0009_lessonprogress_attempts_lessonprogress_score_pct'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='roles',
            field=models.ManyToManyField(
                blank=True,
                related_name='topics',
                to='lms.role',
                verbose_name='Доступно ролям',
            ),
        ),
    ]
