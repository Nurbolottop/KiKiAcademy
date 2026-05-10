from django.conf import settings
from django.db import models


class Role(models.Model):
    class Code(models.TextChoices):
        CLEANER = 'CLEANER', 'Cleaner'
        SENIOR_CLEANER = 'SENIOR_CLEANER', 'Senior cleaner'
        MANAGER = 'MANAGER', 'Manager'
        HR = 'HR', 'HR'
        FOUNDER = 'FOUNDER', 'Founder'

    code = models.CharField(max_length=32, unique=True, choices=Code.choices)
    title = models.CharField(max_length=100)
    is_learning_participant = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self) -> str:
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self) -> str:
        return str(self.user)


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self) -> str:
        return self.title


class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'
        ordering = ['course_id', 'order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['course', 'order'], name='uniq_topic_order_per_course'),
        ]

    def __str__(self) -> str:
        return f"{self.course}: {self.title}"


class Lesson(models.Model):
    class Kind(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        VIDEO = 'VIDEO', 'Video'
        QUIZ = 'QUIZ', 'Quiz'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.TEXT)
    content = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['topic_id', 'order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['topic', 'order'], name='uniq_lesson_order_per_topic'),
        ]

    def __str__(self) -> str:
        return f"{self.topic}: {self.title}"


class RoleCourse(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_roles')
    is_required = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Курс для роли'
        verbose_name_plural = 'Курсы для ролей'
        constraints = [
            models.UniqueConstraint(fields=['role', 'course'], name='uniq_role_course'),
        ]

    def __str__(self) -> str:
        return f"{self.role} -> {self.course}"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    assigned_role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='enrollments')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Назначение курса'
        verbose_name_plural = 'Назначения курсов'
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='uniq_enrollment_user_course'),
        ]
        indexes = [
            models.Index(fields=['user', 'completed_at']),
            models.Index(fields=['course', 'completed_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.course}"


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_items')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Прогресс урока'
        verbose_name_plural = 'Прогресс уроков'
        constraints = [
            models.UniqueConstraint(fields=['enrollment', 'lesson'], name='uniq_progress_enrollment_lesson'),
        ]
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]

    def __str__(self) -> str:
        return f"{self.enrollment} | {self.lesson}"
