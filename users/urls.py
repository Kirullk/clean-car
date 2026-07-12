from django.urls import path, include

from . import views


urlpatterns = [
    path('', views.RegisterView.as_view(), name='register'),
]
