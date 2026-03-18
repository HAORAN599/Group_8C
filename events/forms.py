from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    """
    Form class used by Society Admins to create or update events.
    Uses Bootstrap styling and native HTML5 datetime-local pickers.
    """

    # Explicitly defining datetime fields to support HTML5 'datetime-local' input type
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    )

    class Meta:
        # Mapping the form to the Event model
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time', 'capacity', 'image']

        # Customizing widgets to inject Bootstrap 'form-control' classes for a modern UI
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }