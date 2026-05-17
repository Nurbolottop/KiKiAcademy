from django.db import migrations


def seed_roles(apps, schema_editor):
    Role = apps.get_model('lms', 'Role')

    required = [
        {'code': 'FOUNDER', 'title': 'Founder', 'is_learning_participant': False},
        {'code': 'MANAGER', 'title': 'Менеджер', 'is_learning_participant': True},
        {'code': 'OPERATOR', 'title': 'Оператор', 'is_learning_participant': True},
        {'code': 'HR', 'title': 'HR', 'is_learning_participant': True},
        {'code': 'CLEANER', 'title': 'Клинер', 'is_learning_participant': True},
    ]

    for item in required:
        Role.objects.update_or_create(
            code=item['code'],
            defaults={
                'title': item['title'],
                'is_learning_participant': item['is_learning_participant'],
            },
        )

    Role.objects.filter(code='SENIOR_CLEANER').delete()


def unseed_roles(apps, schema_editor):
    Role = apps.get_model('lms', 'Role')
    Role.objects.filter(code__in=['MANAGER', 'OPERATOR', 'HR', 'CLEANER']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
