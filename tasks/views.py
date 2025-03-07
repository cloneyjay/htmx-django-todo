from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from tasks.forms import TaskForm
from .models import Task


@login_required
def index(request):
    tasks = request.user.tasks.all()
    context = {
        'tasks': tasks,
        'form': TaskForm()
    }
    return render(request, 'tasks/task.html', context)

@login_required
def search_task(request):
    import time
    time.sleep(2)

    query = request.GET.get('search', '')
    tasks = request.user.tasks.filter(title__icontains=query)
    context = {
        'tasks': tasks
    }
    return render(request, 'tsks/partials/task-list.html', context)

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
        context = {
            'task': task
        }
        response = render(request, 'tasks/partials/task-row', context)
        response['HX-Trigger'] = 'task-created'
        return response
    else:
        response = render(request, 'tasks/partials/add-task-modal.html', {'form': form})
        response['HX-Retarget'] = 'task_modal'
        response['HX-Reswap'] = 'outerHTML'
        response['HX-Trigger-After-Settle'] = 'fail'
        return response
 


@login_required
@require_http_methods(["DELETE"])
def delete_task(request, pk):
    task = Task.objects.get(Task, pk=pk, user=request.user)
    task.delete()
    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'task-deleted'
    return response

@login_required
@require_http_methods(["POST"])
def update_task(request, pk):
    task = Task.objects.get(Task, pk=pk, user=request.user)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        task = form.save()
        context = {
            'task': task
        }
        response = render(request, 'tasks/partials/task-row.html', context)
        response['HX-Trigger'] = 'task-updated'
        return response
    else:
        response = render(request, 'tasks/partials/edit-task-modal.html', {'form': form, 'task': task})
        response['HX-Retarget'] = 'task_modal'
        response['HX-Reswap'] = 'outerHTML'
        response['HX-Trigger-After-Settle'] = 'fail'
        return response


