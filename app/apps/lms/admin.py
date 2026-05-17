from django.contrib import admin

from apps.lms import models


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'is_learning_participant')
    list_filter = ('is_learning_participant',)
    search_fields = ('code', 'title')


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roles_display', 'status', 'hired_at', 'fired_at')
    list_filter = ('status', 'roles')
    search_fields = ('user__phone', 'user__email', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)
    filter_horizontal = ('roles',)

    @admin.display(description='Роли')
    def roles_display(self, obj):
        return ', '.join(obj.roles.values_list('title', flat=True))


class TopicInline(admin.TabularInline):
    model = models.Topic
    extra = 0


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'created_at')
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
    search_fields = ('user__phone', 'user__email', 'user__first_name', 'user__last_name', 'course__title')
    autocomplete_fields = ('user', 'course', 'assigned_role')


@admin.register(models.LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'completed_at', 'updated_at')
    list_filter = ('is_completed', 'lesson__topic__course')
    autocomplete_fields = ('enrollment', 'lesson')
