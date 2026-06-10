from django.urls import path

from apps.admin_panel import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    path('employees/', views.employees_list_view, name='employees'),
    path('employees/bulk/', views.employees_bulk_action_view, name='employees_bulk'),
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail_view, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_edit_view, name='employee_edit'),
    path('employees/<int:pk>/roles/toggle/', views.employee_roles_toggle_view, name='employee_roles_toggle'),
    path('employees/<int:pk>/block/', views.employee_block_view, name='employee_block'),
    path('employees/<int:pk>/activate/', views.employee_activate_view, name='employee_activate'),
    path('employees/<int:pk>/fire/', views.employee_fire_view, name='employee_fire'),
    path('employees/<int:pk>/reset-password/', views.employee_reset_password_view, name='employee_reset_password'),
    path('employees/<int:pk>/delete/', views.employee_delete_view, name='employee_delete'),

    path('courses/', views.courses_view, name='courses'),
    path('courses/create/', views.course_create_view, name='course_create'),
    path('courses/reorder/', views.courses_reorder_view, name='courses_reorder'),
    path('courses/<int:pk>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit_view, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete_view, name='course_delete'),

    path('courses/<int:course_pk>/topics/create/', views.topic_create_view, name='topic_create'),
    path('courses/<int:course_pk>/topics/reorder/', views.topics_reorder_view, name='topics_reorder'),
    path('courses/<int:course_pk>/topics/<int:pk>/', views.topic_detail_view, name='topic_detail'),
    path('courses/<int:course_pk>/topics/<int:pk>/edit/', views.topic_edit_view, name='topic_edit'),
    path('courses/<int:course_pk>/topics/<int:pk>/roles/', views.topic_roles_update_view, name='topic_roles_update'),
    path('courses/<int:course_pk>/topics/<int:pk>/delete/', views.topic_delete_view, name='topic_delete'),

    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/create/', views.lesson_create_view, name='lesson_create'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/reorder/', views.lessons_reorder_view, name='lessons_reorder'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:pk>/', views.lesson_edit_view, name='lesson_edit'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:pk>/delete/', views.lesson_delete_view, name='lesson_delete'),

    # Lesson blocks (content)
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/blocks/create/<str:kind>/',
         views.block_create_view, name='block_create'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/blocks/reorder/',
         views.blocks_reorder_view, name='blocks_reorder'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/blocks/<int:pk>/edit/',
         views.block_edit_view, name='block_edit'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/blocks/<int:pk>/delete/',
         views.block_delete_view, name='block_delete'),

    # Quiz questions
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/create/',
         views.question_create_view, name='question_create'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/reorder/',
         views.questions_reorder_view, name='questions_reorder'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/<int:pk>/edit/',
         views.question_edit_view, name='question_edit'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/<int:pk>/delete/',
         views.question_delete_view, name='question_delete'),

    # Quiz answers
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/<int:question_pk>/answers/create/',
         views.answer_create_view, name='answer_create'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/<int:question_pk>/answers/<int:pk>/toggle/',
         views.answer_toggle_view, name='answer_toggle'),
    path('courses/<int:course_pk>/topics/<int:topic_pk>/lessons/<int:lesson_pk>/questions/<int:question_pk>/answers/<int:pk>/delete/',
         views.answer_delete_view, name='answer_delete'),

    path('programs/', views.programs_view, name='programs'),
    path('settings/', views.settings_view, name='settings'),
]
