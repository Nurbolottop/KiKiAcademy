import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0010_topic_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='pass_threshold',
            field=models.PositiveIntegerField(
                default=100,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name='Проходной балл, % (для теста)',
            ),
        ),
    ]
