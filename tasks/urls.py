from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.index, name='index'),
    path('create-task/', views.create_task, name='create_task'),
    path('delete_task/<int:pk>/', views.delete_task, name='delete_task'),
    path('search_task/', views.search_task, name='search_task'),
    path('update_task/<int:pk>/', views.update_task, name='update_task'),
]