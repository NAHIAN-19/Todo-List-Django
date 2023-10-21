from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from Todo_List_App.models import Task, Category, Profile, Activity, CustomUser
from Todo_List_App.forms import CustomUserAdminForm

class TaskAdmin(admin.ModelAdmin):
    list_display = ('taskTitle', 'category', 'dueDate', 'status','important', 'completedDate', 'createdDate', 'user')
    ordering = ('status', 'dueDate',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'completed_tasks_count')

class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_created', 'task_created','task_completed', 'task_edited','task_deleted','last_online')
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'phone','email','is_active')
    list_filter = ('is_active',)
    form = CustomUserAdminForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
admin.site.register(Category, CategoryAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Activity, ActivityAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
