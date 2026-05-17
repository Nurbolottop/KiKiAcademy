from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from apps.lms.models import Enrollment, RoleCourse, UserProfile


@receiver(m2m_changed, sender=UserProfile.roles.through)
def create_enrollments_on_role_add(sender, instance: UserProfile, action, pk_set, **kwargs):
    if action != 'post_add' or not pk_set:
        return

    role_courses = RoleCourse.objects.filter(role_id__in=pk_set).select_related('role', 'course')
    for rc in role_courses:
        Enrollment.objects.get_or_create(
            user=instance.user,
            course=rc.course,
            defaults={'assigned_role': rc.role},
        )


@receiver(post_save, sender=UserProfile)
def sync_user_is_active(sender, instance: UserProfile, **kwargs):
    should_be_active = instance.status == UserProfile.Status.ACTIVE
    if instance.user.is_active != should_be_active:
        instance.user.is_active = should_be_active
        instance.user.save(update_fields=['is_active'])
