from django.urls import path

from . import views


urlpatterns = [
    path('', views.ServiceView.as_view(), name='index'),
    path('times/<str:service>/', views.SlotsTimeView.as_view(), name='times'),
    path('times/<str:service>/create/', views.CreateAppointmentView.as_view(), name='create'),
    path('times/<str:service>/confirm/', views.ConfirmAppointmentView.as_view(), name='appointment_confirm')
    path('appointments/', views.AppointmentsView.as_view(), name='my_appointments'),
]
