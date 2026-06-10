from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0011_lesson_pass_threshold'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='full_access',
            field=models.BooleanField(default=False, verbose_name='Полный доступ ко всем курсам'),
        ),
    ]
