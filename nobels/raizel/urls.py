from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.signin),  # Default URL pattern for the sign-in page
    path('signin/', views.signin, name='signin'),
    path('todo/', TemplateView.as_view(template_name='todo.html'), name='todo'),
    path('about/',TemplateView.as_view(template_name='about.html'), name='about'),
    path('home/', views.raizel, name='raizel'),
    path('running-tasks/', views.running_tasks, name='running_tasks'),
    path('completed-tasks/', views.completed_tasks, name='completed_tasks'),
    path('add-category/', views.add_category, name='add_category'),
    path('all-categories/', views.all_categories, name='all_categories'),
    path('all-categories/<int:category_id>/', views.all_categories, name='filtered_categories'),
    path('mark-task-completed/<int:task_id>/', views.mark_task_completed, name='mark_task_completed'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('clear-history/', views.clear_history, name='clear_history'),
    path('edit-task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('running-tasks/', views.running_tasks, name='running_tasks'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
