from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from Todo_List_App.models import Task, Category, Profile, CustomUser
from Todo_List_App.forms import CustomUserAdminForm

class TaskAdmin(admin.ModelAdmin):
    list_display = ('taskTitle', 'category', 'dueDate','important', 'completedDate', 'createdDate', 'user', 'status', 'description')
    ordering = ('status', 'dueDate',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'completed_tasks_count')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'phone','email')
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
admin.site.register(CustomUser, CustomUserAdmin)
