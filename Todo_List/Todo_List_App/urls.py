from django.urls import path, include
from . import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, TaskViewSet, CategoryViewSet, ProfileViewSet, ActivityViewSet
from rest_framework.authtoken.views import obtain_auth_token
from .views import TaskView, CategoryView, ProfileView, ActivityView, CustomUserView
router = DefaultRouter()
router.register(r'api/users', CustomUserViewSet)
router.register(r'api/tasks', TaskViewSet)
router.register(r'api/categories', CategoryViewSet)
router.register(r'api/profiles', ProfileViewSet)
router.register(r'api/activities', ActivityViewSet)
urlpatterns = [
    path('', TemplateView.as_view(template_name='todo.html')),
    path('signin/', views.signin, name='signin'),
    path('todo/', TemplateView.as_view(template_name='todo.html'), name='todo'),
    path('home/', views.Todo_List_App, name='Todo_List_App'),
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
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('delete-account/<int:user_id>/delete/', views.delete_account, name='delete_account'),
    path('reset-password/<int:user_id>/', views.reset_password, name='reset_password'),
    path('export/csv/', views.export_tasks, name='export_tasks'),
    path('export/pdf/', views.ExportPDF.as_view(), name='export_pdf'),
    path('api/', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('taskview/', TaskView.as_view(), name='taskview'),
    path('categoryview/', CategoryView.as_view(), name='categoryview'),
    path('profileview/', ProfileView.as_view(), name='profileview'),
    path('activityview/', ActivityView.as_view(), name='activityview'),
    path('customuserview/', CustomUserView.as_view(), name='customuserview'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
