from django.urls import path

from apps.lms import views

urlpatterns = [
    path('lessons/<int:pk>/', views.lesson_view, name='lesson_view'),
    path('lessons/<int:pk>/complete/', views.lesson_complete_view, name='lesson_complete'),
    path('lessons/<int:pk>/quiz-submit/', views.lesson_quiz_submit_view, name='lesson_quiz_submit'),
    path('lessons/<int:pk>/history/', views.lesson_quiz_history_view, name='lesson_quiz_history'),
    path('attempts/<int:pk>/', views.quiz_attempt_view, name='quiz_attempt'),
]
