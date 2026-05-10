from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from apps.lms import models


def _is_founder(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    if not profile or not profile.role:
        return False
    return profile.role.code == models.Role.Code.FOUNDER


class UserProfileInline(admin.StackedInline):
    model = models.UserProfile
    can_delete = False
    extra = 1
    min_num = 1
    max_num = 1
    validate_min = True
    autocomplete_fields = ('role',)


class UserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline,)

    def has_view_permission(self, request, obj=None):
        return _is_founder(request.user)

    def has_add_permission(self, request):
        return _is_founder(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_founder(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_founder(request.user)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'is_learning_participant')
    list_filter = ('is_learning_participant',)
    search_fields = ('code', 'title')


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
    autocomplete_fields = ('user',)


class TopicInline(admin.TabularInline):
    model = models.Topic
    extra = 0


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('title',)
    inlines = (TopicInline,)


class LessonInline(admin.TabularInline):
    model = models.Lesson
    extra = 0


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title',)
    inlines = (LessonInline,)
    autocomplete_fields = ('course',)


@admin.register(models.Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'order', 'kind', 'is_published')
    list_filter = ('kind', 'is_published', 'topic__course')
    search_fields = ('title',)
    autocomplete_fields = ('topic',)


@admin.register(models.RoleCourse)
class RoleCourseAdmin(admin.ModelAdmin):
    list_display = ('role', 'course', 'is_required')
    list_filter = ('role', 'is_required')
    autocomplete_fields = ('role', 'course')


@admin.register(models.Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'assigned_role', 'started_at', 'completed_at')
    list_filter = ('assigned_role', 'course', 'completed_at')
    search_fields = ('user__username', 'user__email', 'course__title')
    autocomplete_fields = ('user', 'course', 'assigned_role')


@admin.register(models.LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'completed_at', 'updated_at')
    list_filter = ('is_completed', 'lesson__topic__course')
    autocomplete_fields = ('enrollment', 'lesson')
