from .models import Task
from django import forms
from django.core.exceptions import ValidationError


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
        if Task.objects.filter(title=title).exists():
            raise ValidationError('Task with this title already exists')
        return title
    
    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']
        try:
            task = Task.objects.get(title=self.cleaned_data['title'])
            if due_date < task.created_at:
                raise ValidationError('Due date cannot be earlier than the creation date')
        except Task.DoesNotExist:
            pass
            raise ValidationError('Due date cannot be earlier than the creation date')
        return due_date


    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'})
        }