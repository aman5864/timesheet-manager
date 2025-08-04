from django import forms
from timesheet_backend.models import TimesheetEntry
from django.contrib.auth.forms import UserCreationForm
from timesheet_backend.models import CustomUser
from django.contrib.auth.forms import AuthenticationForm

class TimesheetEntryForm(forms.ModelForm):
    class Meta:
        model = TimesheetEntry
        fields = ['date', 'task', 'subtask', 'time_taken', 'ticket_number', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)

class OTPBypassAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass
