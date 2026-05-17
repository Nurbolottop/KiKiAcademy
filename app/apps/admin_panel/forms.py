from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.accounts.utils import normalize_phone
from apps.base.models import Settings
from apps.lms.models import Answer, Course, Lesson, LessonBlock, Question, Role, Topic, UserProfile


User = get_user_model()


def _default_password() -> str:
    settings_obj = Settings.objects.first()
    if settings_obj and settings_obj.default_staff_password:
        return settings_obj.default_staff_password
    return getattr(settings, 'DEFAULT_STAFF_PASSWORD', '12345678')


class EmployeeForm(forms.Form):
    phone = forms.CharField(label='Телефон', max_length=32)
    first_name = forms.CharField(label='Имя', max_length=150, required=False)
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False)
    email = forms.EmailField(label='Email', required=False)
    roles = forms.ModelMultipleChoiceField(
        label='Роли',
        queryset=Role.objects.exclude(code=Role.Code.FOUNDER).order_by('title'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    status = forms.ChoiceField(
        label='Статус',
        choices=UserProfile.Status.choices,
        initial=UserProfile.Status.ACTIVE,
    )

    def __init__(self, *args, instance: UserProfile | None = None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None:
            user = instance.user
            self.fields['phone'].initial = user.phone
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['roles'].initial = instance.roles.all()
            self.fields['status'].initial = instance.status

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get('phone'))
        if not phone:
            raise forms.ValidationError('Укажите корректный номер телефона')

        qs = User.objects.filter(phone=phone)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('Пользователь с таким телефоном уже существует')
        return phone


class EmployeeCreateForm(EmployeeForm):
    password = forms.CharField(
        label='Пароль',
        required=False,
        help_text='Если пусто — будет использован пароль по умолчанию из настроек сайта',
        widget=forms.PasswordInput(render_value=True),
    )

    def save(self) -> UserProfile:
        data = self.cleaned_data
        password = data.get('password') or _default_password()

        user = User(
            phone=data['phone'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email', ''),
        )
        user.set_password(password)
        user.save()

        profile = UserProfile.objects.create(user=user, status=data['status'])
        if data.get('roles'):
            profile.roles.set(data['roles'])
        return profile


class EmployeeEditForm(EmployeeForm):
    def save(self) -> UserProfile:
        if self.instance is None:
            raise RuntimeError('EmployeeEditForm requires instance')

        data = self.cleaned_data
        user = self.instance.user
        user.phone = data['phone']
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.email = data.get('email', '')
        user.save()

        self.instance.status = data['status']
        self.instance.save()
        self.instance.roles.set(data.get('roles') or [])
        return self.instance


class PasswordResetForm(forms.Form):
    password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(render_value=True),
        min_length=4,
    )


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = (
            'title', 'description', 'logo', 'icon',
            'email', 'phone', 'locate', 'work_schedule', 'default_staff_password',
            'whatsapp', 'telegram', 'instagram', 'facebook',
        )
        widgets = {
            'description': CKEditorUploadingWidget(config_name='admin_panel'),
        }


# ─── COURSE / TOPIC / LESSON ──────────────────────────────────

class CourseForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        label='Роли, которым назначается курс',
        queryset=Role.objects.exclude(code=Role.Code.FOUNDER).order_by('title'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Сотрудники с этими ролями получат курс автоматически',
    )

    class Meta:
        model = Course
        fields = ('title', 'description', 'icon', 'order')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['roles'].initial = Role.objects.filter(
                role_courses__course=self.instance
            ).distinct()

    def save(self, commit: bool = True) -> Course:
        course = super().save(commit=commit)
        if commit:
            self._sync_roles(course)
        return course

    def save_m2m(self):  # type: ignore[override]
        super().save_m2m() if hasattr(super(), 'save_m2m') else None
        if self.instance and self.instance.pk:
            self._sync_roles(self.instance)

    def _sync_roles(self, course: Course) -> None:
        from apps.lms.models import RoleCourse
        selected = set(self.cleaned_data.get('roles', []).values_list('id', flat=True))
        existing = set(RoleCourse.objects.filter(course=course).values_list('role_id', flat=True))
        for role_id in selected - existing:
            RoleCourse.objects.create(course=course, role_id=role_id)
        RoleCourse.objects.filter(course=course, role_id__in=existing - selected).delete()


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('title',)


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('title', 'kind', 'description', 'is_published')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Краткое введение к уроку…'}),
        }


# ─── LESSON CONTENT BLOCKS ────────────────────────────────────

class BlockTextForm(forms.ModelForm):
    class Meta:
        model = LessonBlock
        fields = ('text',)
        widgets = {
            'text': CKEditorUploadingWidget(config_name='admin_panel'),
        }


class BlockImageForm(forms.ModelForm):
    class Meta:
        model = LessonBlock
        fields = ('image', 'caption')
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Подпись (необязательно)'}),
        }


class BlockVideoForm(forms.ModelForm):
    class Meta:
        model = LessonBlock
        fields = ('video_url', 'caption')
        widgets = {
            'video_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=... или https://vimeo.com/...'}),
            'caption': forms.TextInput(attrs={'placeholder': 'Подпись (необязательно)'}),
        }


# ─── QUIZ ─────────────────────────────────────────────────────

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Текст вопроса…'}),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text', 'is_correct')
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Вариант ответа'}),
        }

