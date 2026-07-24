from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (AppointmentViewSet, BoxViewSet, ServiceSlotsView,
                    ServiceViewSet, WasherViewSet)


router_v1 = DefaultRouter()
router_v1.register('services', ServiceViewSet, basename='service')
router_v1.register('boxes', BoxViewSet, basename='box')
router_v1.register('appointments', AppointmentViewSet, basename='appointment')
router_v1.register('washers', WasherViewSet, basename='washer')


urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/services/<int:service_id>/slots/', ServiceSlotsView.as_view(),
         name='service-slots'),
    path('v1/auth/', include('djoser.urls')),
    path('v1/auth/', include('djoser.urls.jwt')),
]
