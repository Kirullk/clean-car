from django.urls import path

from . import views


urlpatterns = [
    path('', views.ServiceView.as_view(),
         name='index'),
    path('times/<int:id>/', views.SlotsTimeView.as_view(),
         name='times'),
    path('times/<int:id>/create/', views.CreateAppointmentView.as_view(),
         name='create'),
    path('times/<int:id>/confirm/', views.ConfirmAppointmentView.as_view(),
         name='appointment_confirm'),
    path('appointments/', views.AppointmentsView.as_view(),
         name='my_appointments'),
    path('my-washer/', views.MyWasherView.as_view(),
         name='my_washer'),
    path('my-washer/edit/', views.WasherEditView.as_view(),
         name='washer_edit')
]
