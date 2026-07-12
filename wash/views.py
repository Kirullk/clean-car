from datetime import datetime, timezone, timedelta

from django.views.generic import FormView, ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse

from .models import Service, Box, Appointment, Washer
from .forms import AppointmentForm
from .utils import generate_slots


class ServiceView(ListView):
    queryset = Service.objects.all()
    template_name = 'wash/index.html'
    context_object_name = 'services'
    paginate_by = 6


class SlotsTimeView(DetailView):
    template_name = 'wash/slots.html'

    def get_object(self):
        return get_object_or_404(Service, name=self.kwargs['service'], is_active=True)

    def get(self, request, *args, **kwargs):
        selected_slot = request.GET.get('slot')
        box_id = request.GET.get('box_id')
        washer = request.GET.get('washer')
        date = request.GET.get('date')

        if selected_slot and box_id and date and washer:
            url = reverse('create', args=[self.kwargs['service']])
            return redirect(f'{url}?slot={selected_slot}&box={box_id}&date={date}&washer={washer}')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        box_id = self.request.GET.get('box_id')
        date_str = self.request.GET.get('date')

        if box_id:
            box_object = get_object_or_404(
                Box,
                id=box_id,
                status=Box.StatusChoices.WORKING
            )
        else:
            box_object = Box.objects.filter(
                status=Box.StatusChoices.WORKING
            ).first()

        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()

        all_appointments = box_object.appointments.filter(
            time__date=date
        )

        available_slots, washer = generate_slots(all_appointments,
                                                 self.object, date)
        context['available_slots'] = available_slots
        context['washer'] = washer
        context['dates'] = [
            timezone.now().date() + timedelta(days=i) for i in range(7)
        ]
        context['boxes'] = Box.objects.filter(status=Box.StatusChoices.WORKING)
        context['selected_box'] = box_object
        context['selected_date'] = date

        return context


class CreateAppointmentView(FormView):
    form_class = AppointmentForm
    template_name = 'wash/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, name=kwargs['service'], is_active=True)
        self.selected_slot = request.GET.get('slot')
        self.box = get_object_or_404(Box, pk=request.GET.get('box'))
        self.washer = get_object_or_404(Washer, pk=request.GET.get('washer'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context
    
    def form_valid(self, form):
        # Сохраняем данные в сессию
        self.request.session['appointment_data'] = {
            'service_id': self.service.id,
            'box_id': self.box.id,
            'washer_id': self.washer.id,
            'slot': self.selected_slot,
            'client_name': form.cleaned_data['client_name'],
            'phone_number': str(form.cleaned_data['phone_number']),
        }
        return redirect('appointment_confirm')


class ConfirmAppointmentView(TemplateView):
    template_name = 'wash/confirm.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.session.get('appointment_data')
        
        if not data:
            return redirect('index')
        
        context['service'] = get_object_or_404(Service, pk=data['service_id'])
        context['box'] = get_object_or_404(Box, pk=data['box_id'])
        context['washer'] = get_object_or_404(Washer, pk=data['washer_id'])
        context['slot_datetime'] = datetime.fromisoformat(data['slot'])
        context['client_name'] = data['client_name']
        context['phone_number'] = data['phone_number']
        
        return context
    
    def post(self, request, *args, **kwargs):
        data = request.session.get('appointment_data')
        
        if not data:
            return redirect('index')

        appointment = Appointment.objects.create(
            service_id=data['service_id'],
            box_id=data['box_id'],
            washer_id=data['washer_id'],
            date=datetime.fromisoformat(data['slot']),
            client_name=data['client_name'],
            phone_number=data['phone_number'],
            client=request.user if request.user.is_authenticated else None
        )
        
        del request.session['appointment_data']
        
        messages.success(request, 'Вы записаны!')
        return redirect('my_appointments', pk=appointment.pk)



class AppointmentsView(LoginRequiredMixin, ListView):
    template_name = 'wash/appointments.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        return self.request.user.appointments.order_by('-date')
    
    def handle_no_permission(self):
        messages.warning(self.request, 'Войдите в систему, чтобы просмотреть свои записи')
        return redirect('login')
