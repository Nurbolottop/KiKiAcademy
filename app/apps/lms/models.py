from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_resized.forms import ResizedImageField


class Role(models.Model):
    class Code(models.TextChoices):
        CLEANER = 'CLEANER', 'Cleaner'
        MANAGER = 'MANAGER', 'Manager'
        OPERATOR = 'OPERATOR', 'Operator'
        HR = 'HR', 'HR'
        FOUNDER = 'FOUNDER', 'Founder'

    code = models.CharField(max_length=32, unique=True, choices=Code.choices, verbose_name='Код')
    title = models.CharField(max_length=100, verbose_name='Название')
    is_learning_participant = models.BooleanField(default=True, verbose_name='Участвует в обучении')

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self) -> str:
        return self.title


class UserProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Активен'
        BLOCKED = 'BLOCKED', 'Заблокирован'
        FIRED = 'FIRED', 'Уволен'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    roles = models.ManyToManyField(Role, related_name='users', blank=True, verbose_name='Роли')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, verbose_name='Статус')
    points = models.PositiveIntegerField(default=0, verbose_name='Баллы')
    # Полный доступ: видны все курсы, все этапы и уроки открыты (без блокировок).
    full_access = models.BooleanField(default=False, verbose_name='Полный доступ ко всем курсам')
    hired_at = models.DateField(auto_now_add=True, verbose_name='Дата найма')
    fired_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата увольнения')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self) -> str:
        return str(self.user)

    @property
    def is_employed(self) -> bool:
        return self.status == self.Status.ACTIVE


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    icon = models.CharField(max_length=8, blank=True, default='📚', verbose_name='Иконка')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return self.title


class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics', verbose_name='Курс')
    title = models.CharField(max_length=200, verbose_name='Название')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    # Доступ по ролям на уровне темы. Пусто = тема видна всем ролям курса.
    roles = models.ManyToManyField(Role, blank=True, related_name='topics', verbose_name='Доступно ролям')

    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'
        ordering = ['course_id', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.course}: {self.title}"


class Lesson(models.Model):
    class Kind(models.TextChoices):
        CONTENT = 'CONTENT', 'Контент'
        QUIZ = 'QUIZ', 'Тест'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons', verbose_name='Тема')
    title = models.CharField(max_length=200, verbose_name='Название')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.CONTENT, verbose_name='Тип')
    description = models.TextField(blank=True, verbose_name='Описание / введение')
    is_published = models.BooleanField(default=True, verbose_name='Опубликован')
    # Проходной балл теста (%). Используется только для уроков типа QUIZ.
    pass_threshold = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Проходной балл, % (для теста)',
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['topic_id', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.topic}: {self.title}"


class LessonBlock(models.Model):
    """Гибкий блок контента урока: текст, изображение или видео."""
    class Kind(models.TextChoices):
        TEXT = 'TEXT', 'Текст'
        IMAGE = 'IMAGE', 'Изображение'
        VIDEO = 'VIDEO', 'Видео'

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='blocks', verbose_name='Урок')
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.TEXT, verbose_name='Тип блока')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    text = models.TextField(blank=True, verbose_name='Текст')
    image = ResizedImageField(
        force_format='WEBP', quality=82, size=[1600, 1600], keep_meta=False,
        upload_to='lessons/images/', blank=True, null=True, verbose_name='Изображение',
    )
    caption = models.CharField(max_length=255, blank=True, verbose_name='Подпись')
    video_url = models.URLField(blank=True, verbose_name='URL видео (YouTube / Vimeo)')

    class Meta:
        verbose_name = 'Блок урока'
        verbose_name_plural = 'Блоки урока'
        ordering = ['lesson_id', 'order', 'id']

    def __str__(self) -> str:
        return f"{self.lesson} · {self.get_kind_display()} #{self.order}"


class Question(models.Model):
    """Вопрос теста (для уроков типа QUIZ)."""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions', verbose_name='Урок')
    text = models.TextField(verbose_name='Текст вопроса')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['lesson_id', 'order', 'id']

    def __str__(self) -> str:
        return self.text[:60]


class Answer(models.Model):
    """Вариант ответа на вопрос."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    text = models.CharField(max_length=500, verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ['question_id', 'order', 'id']

    def __str__(self) -> str:
        return self.text[:60]


class RoleCourse(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_courses', verbose_name='Роль')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_roles', verbose_name='Курс')
    is_required = models.BooleanField(default=True, verbose_name='Обязательный')

    class Meta:
        verbose_name = 'Курс для роли'
        verbose_name_plural = 'Курсы для ролей'
        constraints = [
            models.UniqueConstraint(fields=['role', 'course'], name='uniq_role_course'),
        ]

    def __str__(self) -> str:
        return f"{self.role} -> {self.course}"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Курс')
    assigned_role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='enrollments', verbose_name='Роль на момент назначения')
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
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress', verbose_name='Назначение')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_items', verbose_name='Урок')
    is_completed = models.BooleanField(default=False, verbose_name='Завершён')
    completed_at = models.DateTimeField(null=True, blank=True)
    # Результаты теста (для уроков типа QUIZ). Для CONTENT остаются нулевыми.
    score_pct = models.PositiveIntegerField(default=0, verbose_name='Последний результат теста, %')
    attempts = models.PositiveIntegerField(default=0, verbose_name='Число попыток')
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


class QuizAttempt(models.Model):
    """История одной попытки прохождения теста — со снимком вопросов и ответов,
    чтобы сотрудник мог потом разобрать свои ошибки."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='quiz_attempts', verbose_name='Пользователь')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name='quiz_attempts', verbose_name='Тест')
    score_pct = models.PositiveIntegerField(default=0, verbose_name='Результат, %')
    correct_count = models.PositiveIntegerField(default=0, verbose_name='Верных ответов')
    total_count = models.PositiveIntegerField(default=0, verbose_name='Всего вопросов')
    passed = models.BooleanField(default=False, verbose_name='Пройден')
    # Снимок: [{question, is_right, answers:[{text, selected, correct}]}]
    detail = models.JSONField(default=list, blank=True, verbose_name='Разбор ответов')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата попытки')

    class Meta:
        verbose_name = 'Попытка теста'
        verbose_name_plural = 'История тестов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'lesson', '-created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user} | {self.lesson} | {self.score_pct}%"
