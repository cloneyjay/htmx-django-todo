from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tasks.forms import TaskForm, UserRegistrationForm
from .models import Task
from django.http import JsonResponse
import json

def register_user(request):
    """
    Handle user registration.
    
    On GET: Render the registration form.
    On POST: Process the form submission, create the user if valid.
    If form is invalid: Return JSON with validation errors.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            # Return a success response that the JS will use to reload the page
            return JsonResponse({'success': True, 'redirect': True}, status=200)
        else:
            # Convert form errors to JSON and return
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            # Add non-field errors if any exist
            if form.non_field_errors():
                errors['non_field_errors'] = [str(error) for error in form.non_field_errors()]
                
            return JsonResponse({'errors': errors}, status=400)
    else:
        # For GET requests, just render the empty form
        form = UserRegistrationForm()
        return render(request, 'tasks/partials/register-modal.html', {'form': form})

def login_user(request):
    """
    Handle user login.
    
    On POST: Authenticate user with provided credentials.
    If successful: Log in the user and redirect to tasks page.
    If unsuccessful: Return an error message.
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful')
            # Return a success response that the JS will use to reload the page
            return JsonResponse({'success': True, 'redirect': True}, status=200)
        else:
            # Return a JSON response with an error message
            return JsonResponse({
                'error': 'Invalid username or password'
            }, status=401)
    else:
        return render(request, 'tasks/partials/login-modal.html')

def logout_user(request):
    """
    Log out the current user and redirect to index page.
    """
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('tasks:index')

def index(request):
    """
    Main view that handles both authenticated and unauthenticated users.
    
    For authenticated users: Display their tasks.
    For unauthenticated users: Show the welcome page.
    """
    # Check if user is authenticated
    if request.user.is_authenticated:
        # Get all tasks for the authenticated user
        tasks = request.user.tasks.all()
        
        # Count completed and pending tasks
        completed_count = tasks.filter(completed=True).count()
        pending_count = tasks.filter(completed=False).count()
        
        context = {
            'tasks': tasks,
            'form': TaskForm(),
            'completed_count': completed_count,
            'pending_count': pending_count
        }
        # Render the task dashboard for authenticated users
        return render(request, 'tasks/task.html', context)
    else:
        # Render the welcome page for unauthenticated users
        return render(request, 'tasks/welcome.html')

@login_required
def search_task(request):
    import time
    time.sleep(2)

    query = request.GET.get('search', '')
    tasks = request.user.tasks.filter(title__icontains=query)
    
    # Count completed and pending tasks in the search results
    completed_count = tasks.filter(completed=True).count()
    pending_count = tasks.filter(completed=False).count()
    
    context = {
        'tasks': tasks,
        'completed_count': completed_count,
        'pending_count': pending_count
    }
    
    # Render both the task list and stats with out-of-band swaps
    response = render(request, 'tasks/partials/task-list.html', context)
    
    # Add the stats section as an out-of-band swap
    stats_html = render(request, 'tasks/partials/stats.html', context).content.decode('utf-8')
    
    # Combine the response content with the out-of-band stats update
    response_content = response.content.decode('utf-8')
    oob_stats = f'<div id="task-stats" hx-swap-oob="true">{stats_html}</div>'
    combined_content = response_content + oob_stats
    response.content = combined_content.encode('utf-8')
    
    return response

@require_http_methods(["POST"])
@login_required
def create_task(request):
    """
    Handle the creation of a new task.
    Accepts POST requests with task data, validates the form, and saves the task.
    Returns an appropriate response based on the form validation.
    """
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        
        # Get all tasks for the authenticated user to refresh the task list
        tasks = request.user.tasks.all()
        
        # Count completed and pending tasks
        completed_count = tasks.filter(completed=True).count()
        pending_count = tasks.filter(completed=False).count()
        
        context = {
            'tasks': tasks,
            'completed_count': completed_count,
            'pending_count': pending_count
        }
        
        # Render both the task list and stats with out-of-band swaps
        response = render(request, 'tasks/partials/task-list.html', context)
        
        # Add the stats section as an out-of-band swap
        stats_html = render(request, 'tasks/partials/stats.html', context).content.decode('utf-8')
        response['HX-Trigger'] = 'task-created'
        
        # Combine the response content with the out-of-band stats update
        response_content = response.content.decode('utf-8')
        oob_stats = f'<div id="task-stats" hx-swap-oob="true">{stats_html}</div>'
        combined_content = response_content + oob_stats
        response.content = combined_content.encode('utf-8')
        
        return response
    else:
        response = render(request, 'tasks/partials/add-task-modal.html', {'form': form})
        response['HX-Retarget'] = '#task_modal'
        response['HX-Reswap'] = 'outerHTML'
        return response
 
@login_required
@require_http_methods(["DELETE"])
def delete_task(request, pk):
    try:
        task = Task.objects.get(pk=pk, user=request.user)
        task.delete()
        
        # Get all tasks to refresh the list with updated counts
        tasks = request.user.tasks.all()
        
        # Count completed and pending tasks
        completed_count = tasks.filter(completed=True).count()
        pending_count = tasks.filter(completed=False).count()
        
        context = {
            'tasks': tasks,
            'completed_count': completed_count,
            'pending_count': pending_count
        }
        
        # Render both the task list and stats with out-of-band swaps
        response = render(request, 'tasks/partials/task-list.html', context)
        
        # Add the stats section as an out-of-band swap
        stats_html = render(request, 'tasks/partials/stats.html', context).content.decode('utf-8')
        response['HX-Trigger'] = json.dumps({
            'task-deleted': {'message': 'Task deleted successfully!'}
        })
        
        # Combine the response content with the out-of-band stats update
        response_content = response.content.decode('utf-8')
        oob_stats = f'<div id="task-stats" hx-swap-oob="true">{stats_html}</div>'
        combined_content = response_content + oob_stats
        response.content = combined_content.encode('utf-8')
        
        return response
    except Task.DoesNotExist:
        return HttpResponse("Task not found", status=404)

@login_required
@require_http_methods(["GET", "POST"])
def update_task(request, pk):
    try:
        task = Task.objects.get(pk=pk, user=request.user)
        
        if request.method == 'GET':
            form = TaskForm(instance=task)
            context = {
                'form': form,
                'task': task
            }
            return render(request, 'tasks/partials/edit-task-modal.html', context)
        
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save(commit=False)
            # Handle the completed checkbox separately since it's not part of TaskForm
            completed = request.POST.get('completed', False)
            updated_task.completed = completed == 'on'
            updated_task.save()
            
            # Get all tasks to refresh the list
            tasks = request.user.tasks.all()
            
            # Count completed and pending tasks
            completed_count = tasks.filter(completed=True).count()
            pending_count = tasks.filter(completed=False).count()
            
            context = {
                'tasks': tasks,
                'completed_count': completed_count,
                'pending_count': pending_count
            }
            
            # Render both the task list and stats with out-of-band swaps
            response = render(request, 'tasks/partials/task-list.html', context)
            
            # Add the stats section as an out-of-band swap
            stats_html = render(request, 'tasks/partials/stats.html', context).content.decode('utf-8')
            response['HX-Trigger'] = json.dumps({
                'task-updated': {'message': 'Task updated successfully!'}
            })
            
            # Combine the response content with the out-of-band stats update
            response_content = response.content.decode('utf-8')
            oob_stats = f'<div id="task-stats" hx-swap-oob="true">{stats_html}</div>'
            combined_content = response_content + oob_stats
            response.content = combined_content.encode('utf-8')
            
            return response
        else:
            # Return the form with errors to the edit modal
            context = {
                'form': form,
                'task': task
            }
            response = render(request, 'tasks/partials/edit-task-modal.html', context)
            response['HX-Retarget'] = '#edit-task-modal-container'
            response['HX-Reswap'] = 'innerHTML'
            return response
    except Task.DoesNotExist:
        return HttpResponse("Task not found", status=404)

@login_required
@require_http_methods(["POST"])
def toggle_complete(request, pk):
    try:
        task = Task.objects.get(pk=pk, user=request.user)
        task.completed = not task.completed
        task.save()
        
        # Get all tasks to refresh the list with updated counts
        tasks = request.user.tasks.all()
        
        # Count completed and pending tasks
        completed_count = tasks.filter(completed=True).count()
        pending_count = tasks.filter(completed=False).count()
        
        context = {
            'tasks': tasks,
            'completed_count': completed_count,
            'pending_count': pending_count
        }
        
        # Render both the task list and stats with out-of-band swaps
        response = render(request, 'tasks/partials/task-list.html', context)
        
        # Add the stats section as an out-of-band swap
        stats_html = render(request, 'tasks/partials/stats.html', context).content.decode('utf-8')
        response['HX-Trigger'] = json.dumps({
            'task-updated': {'message': 'Task status updated!'}
        })
        
        # Combine the response content with the out-of-band stats update
        response_content = response.content.decode('utf-8')
        oob_stats = f'<div id="task-stats" hx-swap-oob="true">{stats_html}</div>'
        combined_content = response_content + oob_stats
        response.content = combined_content.encode('utf-8')
        
        return response
    except Task.DoesNotExist:
        return HttpResponse("Task not found", status=404)


