from django import forms
from .models import Resource, Topic, Rating

class ResourceForm(forms.ModelForm):
    topics = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Темы'
    )

    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'url', 'file', 'topics']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={'placeholder': 'Поиск материалов...'})
    )
    resource_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + Resource.TYPE_CHOICES,
        required=False,
        label='Тип материала'
    )
    topic = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        required=False,
        label='Тема',
        empty_label='Все темы'
    )
    date_from = forms.DateField(
        required=False,
        label='С даты',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label='По дату',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название темы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание темы (необязательно)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'width: 60px; height: 38px; padding: 0;'
            }),
        }
        labels = {
            'name': 'Название темы',
            'description': 'Описание',
        }