from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0014_quizattempt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='code',
            field=models.CharField(
                choices=[
                    ('CLEANER', 'Cleaner'),
                    ('MANAGER', 'Manager'),
                    ('OPERATOR', 'Operator'),
                    ('HR', 'HR'),
                    ('SMM', 'SMM / Мобилограф'),
                    ('FOUNDER', 'Founder'),
                ],
                max_length=32, unique=True, verbose_name='Код'),
        ),
    ]
