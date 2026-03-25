from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Event, User

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
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_dt = cleaned_data.get('start_time')
        end_dt = cleaned_data.get('end_time')

        if start_dt and end_dt and end_dt <= start_dt:
            self.add_error('end_time', 'End time must be later than the start time.')

        return cleaned_data

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')

        if capacity is not None and capacity < 1:
            raise forms.ValidationError('Capacity must be at least 1.')

        return capacity


class AccountPhoneForm(forms.ModelForm):
    """Updates the phone number used on the account."""

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'autocomplete': 'tel',
            }
        ),
    )

    class Meta:
        model = User
        fields = ['phone_number']

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get('phone_number') or '').strip()

        if not phone_number:
            raise forms.ValidationError('Please enter a phone number.')

        if User.objects.exclude(pk=self.instance.pk).filter(phone_number=phone_number).exists():
            raise forms.ValidationError('This phone number is already in use.')

        return phone_number


class StyledPasswordChangeForm(PasswordChangeForm):
    """Password change form with app styling hooks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        labels = {
            'old_password': 'Current Password',
            'new_password1': 'New Password',
            'new_password2': 'Confirm New Password',
        }

        placeholders = {
            'old_password': 'Enter your current password',
            'new_password1': 'Enter a new password',
            'new_password2': 'Re-enter the new password',
        }

        for field_name, field in self.fields.items():
            field.label = labels.get(field_name, field.label)
            field.help_text = None
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': placeholders.get(field_name, ''),
                'autocomplete': 'current-password' if field_name == 'old_password' else 'new-password',
            })


class AccountDeletionForm(forms.Form):
    """Confirms the user's password before account deletion."""

    current_password = forms.CharField(
        label='Current Password',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your current password',
                'autocomplete': 'current-password',
            }
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')

        if not self.user.check_password(password):
            raise forms.ValidationError('Enter your current password to delete your account.')

        return password


class CheckInTicketForm(forms.Form):
    """Allows organisers to validate a ticket reference code at check-in."""

    ticket_code = forms.CharField(
        label='Reference Code',
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Reference code',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'autocapitalize': 'characters',
            }
        ),
    )

    def clean_ticket_code(self):
        ticket_code = (self.cleaned_data.get('ticket_code') or '').strip().upper()

        if not ticket_code:
            raise forms.ValidationError('Enter a ticket code to check in an attendee.')

        return ticket_code
