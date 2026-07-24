from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response

from wash.models import Appointment, Box, Service, Washer
from wash.utils import get_free_slots
from .serializer import AppointmentSerializer, BoxSerializer, ServiceSerializer, WasherSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(
            is_active=True,
            washer_category__in=Washer.objects.filter(
                is_active=True
            ).values_list('category', flat=True).distinct()
        ).prefetch_related('washer_category')
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all().order_by('number')
    serializer_class = BoxSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            client=self.request.user
        ).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated()]


class WasherViewSet(viewsets.ModelViewSet):
    queryset = Washer.objects.filter(is_active=True)
    serializer_class = WasherSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class ServiceSlotsView(APIView):

    def get(self, request, service_id):
        service = get_object_or_404(Service, id=service_id, is_active=True)
        date_str = request.GET.get('date')
        date = datetime.strptime(date_str, '%Y.%d.%m'
                                 ).date() if date_str else timezone.now(
                                 ).date()

        boxes = service.boxes.filter(status=Box.StatusChoices.WORKING)
        box = request.GET.get('box')
        if not box:
            box = service.boxes.all().order_by('number').first()
        else:
            box = Box.objects.get(number=box)
        available_slots = []

        slots = get_free_slots(service, date, box)
        for slot_time, washer in slots:
            available_slots.append({
                'time': slot_time.strftime('%H:%M'),
                'washer': washer.name,
                'washer_id': washer.id
            })

        return Response({
            'service': {
                'id': service.id,
                'name': service.name,
                'price': str(service.price)
            },
            'available_slots': available_slots,
            'boxes': [box.number for box in boxes],
            'dates': [(timezone.now() + timedelta(days=day)).date(
                        ).isoformat() for day in range(7)],
            'selected_date': date.isoformat(),
            'selected_box': box.number
        })
