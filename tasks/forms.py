from .models import Task, User
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone


class TaskForm(forms.ModelForm):
    title = forms.CharField( 
                                widget=forms.TextInput(attrs={
                                'class': 'input input-bordered w-full',
                                'placeholder': 'Task Name',}),
                                required = True
                            )
    description = forms.CharField(
                                    widget=forms.Textarea(attrs={
                                    'class': 'textarea textarea-bordered w-full',
                                    'placeholder': 'Task Description',}),
                                    required = False
                                )
    due_date = forms.DateField(
                                widget=forms.DateInput(attrs={
                                'class': 'input input-bordered w-full',
                                'type': 'date',}),
                                required = True
                            )
    
    def clean_title(self):
        title = self.cleaned_data['title']
        # Only check for duplicate titles within the user's own tasks
        if self.instance.pk is None:  # New task
            user = self.instance.user if hasattr(self.instance, 'user') else None
            if user and Task.objects.filter(title=title, user=user).exists():
                raise ValidationError('You already have a task with this title')
        return title
    
    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']
        # Only validate the due date if it's provided
        if due_date and due_date < timezone.now().date():
            raise ValidationError('Due date cannot be in the past')
        return due_date

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'})
        }


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Username',
        }),
        required=True
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Email',
        }),
        required=True
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Password',
        }),
        required=True
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm Password',
        }),
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']