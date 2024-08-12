from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Task-related URLs
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/running/', views.running_tasks, name='running_tasks'),
    path('tasks/completed/', views.completed_tasks, name='completed_tasks'),
    path('tasks/export/csv/', views.export_tasks, name='export_tasks'),
    path('tasks/export/pdf/', views.ExportPDF.as_view(), name='export_pdf'),
    path('tasks/mark-completed/<str:task_id>/', views.mark_task_completed, name='mark_task_completed'),
    path('tasks/delete/<str:task_id>/', views.delete_task, name='delete_task'),
    path('tasks/edit/<str:task_id>/', views.edit_task, name='edit_task'),
    path('tasks/clear-history/', views.clear_history, name='clear_history'),
    # Category-related URLs
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/all/', views.all_categories, name='all_categories'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),

    # User profile and account URLs
    path('account/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('delete-account/<str:user_id>/', views.delete_account, name='delete_account'),

    # Password reset and email verification URLs
    path('password/reset/<str:user_id>/', views.reset_password, name='reset_password'),
    path('email/send-verification/<str:user_id>/', views.send_verification_email, name='send_verification_email'),
    path('email/verify/', views.verify_email, name='verify_email'),
    path('account/find/', views.findAccount, name='findAccount'),
    path('account/send-reset-link/', views.sendResetLink, name='sendResetLink'),
    path('account/check-reset-link/', views.checkResetLink, name='checkResetLink'),

    # AJAX/utility URLs
    path('validate-field/', views.validate_field, name='validate_field'),
    path('invalidate-session/', views.invalidate_session, name='invalidate_session'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
