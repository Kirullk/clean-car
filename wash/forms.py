from django import forms

from .models import Appointment, Washer


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('client_name', 'phone_number',)


class WasherForm(forms.ModelForm):
    class Meta:
        model = Washer
        fields = ('name', 'phone',)
