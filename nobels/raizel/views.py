from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (AuthenticationForm, PasswordChangeForm,
                                       UserCreationForm)
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from raizel.models import Category, Task, Profile
from .forms import PasswordChangeForm, ProfileForm, SignInForm, SignUpForm


#######################this fucntion is used to signup
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = Profile.objects.create(user=user)
            profile_form = ProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully!')
            return redirect('signin')
    else:
        form = SignUpForm()

    return render(request, 'Sign_up.html', {'form': form})

#######################this function is used for signin
def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # Set session expiry
                if remember_me:
                    request.session.set_expiry(timedelta(days=7).total_seconds())
                else:
                    request.session.set_expiry(0)

                return redirect('todo')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'Sign_in.html', context)

#######################this function is used for signout
@login_required
def logout_view(request):
    logout(request)
    return redirect('signin')

#######################this function shows and edit information of that user
@login_required
def profile(request):
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=user)
        profile.save()

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        password_form = PasswordChangeForm(user, request.POST)

        if form.is_valid():
            if request.POST['change_password'] == 'change':
                if password_form.is_valid():
                    password_form.save()
                    update_session_auth_hash(request, user) 

            user.email = request.POST['email']
            user.save()
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
        password_form = PasswordChangeForm(user)

    context = {'form': form, 'password_form': password_form}
    return render(request, 'profile.html', context)

#######################this function is used for ADDING task for that user
@login_required
def raizel(request):
    categories = Category.objects.filter(user=request.user)
    context = {'categories': categories, 'success': False}

    if request.method == "POST":
        title = request.POST['title']
        category_id = request.POST['category']
        category = Category.objects.get(id=category_id)
        due_date = request.POST['due_date']
        due_time = request.POST['dueTime']

        due_datetime = datetime.strptime(f"{due_date} {due_time}", '%Y-%m-%d %H:%M')
        min_due_datetime = timezone.now() + timedelta(minutes=5)
        due_datetime = timezone.make_aware(due_datetime, timezone.get_current_timezone())

        if due_datetime <= min_due_datetime:
            messages.error(request, f"Due datetime must be at least 5 minutes from now. You entered {due_datetime.strftime('%Y-%m-%d |  %H:%M')}.")
            due_datetime = timezone.now() + timedelta(minutes=5)

        task = Task(
            taskTitle=title,
            category=category,
            dueDate=due_datetime,
            user=request.user
        )
        task.save()
        context['success'] = True

    if not categories:
        context['no_categories'] = True

    running_tasks = Task.objects.filter(completed=False)
    context['running_tasks'] = running_tasks
    return render(request, 'index.html', context)

#######################this function shows all the running tasks of that user
@login_required
def running_tasks(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', '')

    tasks = Task.objects.filter(user=request.user,completed=False)

    if search_query:
        tasks = tasks.filter(taskTitle__icontains=search_query)

    if sort_by == 'asc':
        tasks = tasks.order_by('dueDate')
    elif sort_by == 'desc':
        tasks = tasks.order_by(F('dueDate').desc())

    context = {
        'running_tasks': tasks,
        'search_query': search_query,
    }
    return render(request, 'tasks.html', context)

#######################this function edits the specific running task of that user
@login_required  
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    categories = Category.objects.all()

    if request.method == "POST":
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)

        if category is None:
            return HttpResponse("Category not found", status=404)

        due_date = request.POST.get('due_date')
        due_time = request.POST.get('dueTime')

        due_datetime = datetime.strptime(f"{due_date} {due_time}", '%Y-%m-%d %H:%M')
        min_due_datetime = timezone.now() + timedelta(minutes=5)
        due_datetime = timezone.make_aware(due_datetime, timezone.get_current_timezone())

        if due_datetime <= min_due_datetime:
            due_datetime = timezone.now() + timedelta(minutes=5)

        task.taskTitle = title
        task.category = category
        task.dueDate = due_datetime
        task.save()

        messages.success(request, "Task updated successfully!")

        return redirect('running_tasks') 

    context = {'task': task, 'categories': categories}
    return render(request, 'edit.html', context)

#######################this fucntion is used for completing tasks 
@require_POST
def mark_task_completed(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.completed = True
    task.completedDate = timezone.now()
    task.save()

    profile = Profile.objects.get(user=request.user)
    profile.completed_tasks_count += 1
    profile.save()

    messages.success(request, f'Task "{task.taskTitle}" marked as completed successfully. It has been moved to the Completed Tasks tab.')
    return redirect('running_tasks')

#######################this function deletes that specific task details from running tasks of that user
@login_required 
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    messages.success(request, f'Task "{task.taskTitle}" has been deleted successfully.')
    return redirect('running_tasks')

#######################this fucntion shows the completed tasks of that user
@login_required
def completed_tasks(request):
    sort_by = request.GET.get('sort_by', '')
    search_query = request.GET.get('search', '')
    
    completed_tasks = Task.objects.filter(user=request.user,completed=True)
    
    if search_query:
        completed_tasks = completed_tasks.filter(taskTitle__icontains=search_query)
    
    if sort_by == 'asc':
        completed_tasks = completed_tasks.order_by('dueDate')
    elif sort_by == 'desc':
        completed_tasks = completed_tasks.order_by(F('dueDate').desc())
        
    context = {
        'completed_tasks':completed_tasks,
        'search_query': search_query,
    }
        
    return render(request, 'completed.html', context)

#######################this function clears all those completed task details of that user
@login_required
def clear_history(request):
    Task.objects.filter(Q(completed=True)).delete()
    messages.success(request, 'Completed tasks history has been cleared.')
    return redirect('completed_tasks')

#######################this function adds a category for that user
@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST['name']
        category = Category(name=name, user=request.user)
        category.save()

    categories = Category.objects.filter(user=request.user)
    context = {'categories': categories, 'success': False}
    return render(request, 'add_category.html', context)

#######################this function is used to show the categories and all those tasks that the user has
@login_required
def all_categories(request, category_id=None):
    categories = Category.objects.filter(user=request.user)
    tasks = Task.objects.all()

    if category_id is not None:
        tasks = tasks.filter(category_id=category_id)

    context = {
        'categories': categories,
        'tasks': tasks
    }
    if not categories:
        context['no_categories'] = True
    return render(request, 'all_categories.html', context)

#######################this function deletes specific category along with those associated tasks of that user
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    category.delete()
    return redirect('all_categories')
