from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.utils import normalize_phone
from apps.lms.models import Role, UserProfile


class Command(BaseCommand):
    help = 'Создать пользователя с ролью FOUNDER (администратор платформы)'

    def add_arguments(self, parser):
        parser.add_argument('--phone', required=True, help='Номер телефона администратора')
        parser.add_argument('--password', required=True, help='Пароль')
        parser.add_argument('--first-name', default='', help='Имя')
        parser.add_argument('--last-name', default='', help='Фамилия')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        phone = normalize_phone(options['phone'])
        if not phone:
            raise CommandError('Неверный номер телефона')

        founder_role, _ = Role.objects.get_or_create(
            code=Role.Code.FOUNDER,
            defaults={'title': 'Основатель', 'is_learning_participant': False},
        )

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                'first_name': options['first_name'],
                'last_name': options['last_name'],
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if not created:
            user.first_name = options['first_name'] or user.first_name
            user.last_name = options['last_name'] or user.last_name
            user.is_staff = True
            user.is_superuser = True
        user.set_password(options['password'])
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.roles.add(founder_role)

        action = 'создан' if created else 'обновлён'
        self.stdout.write(self.style.SUCCESS(f'Администратор {action}: {user} ({phone})'))
