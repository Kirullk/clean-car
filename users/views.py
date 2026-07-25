from django.views.generic import CreateView
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)
