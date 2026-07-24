from datetime import datetime, timezone, timedelta

from django.views.generic import (DetailView, FormView, ListView,
                                  TemplateView, UpdateView)
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse_lazy

from .models import Appointment, Box, Service, Washer
from .forms import AppointmentForm, WasherForm
from .utils import get_free_slots


class ServiceView(ListView):
    template_name = 'wash/index.html'
    context_object_name = 'services'
    paginate_by = 5

    def get_queryset(self):
        return Service.objects.filter(
            is_active=True,
            washer_category__in=Washer.objects.filter(
                is_active=True
            ).values_list('category', flat=True).distinct()
        ).prefetch_related('washer_category')


class SlotsTimeView(DetailView):
    template_name = 'wash/slots.html'
    context_object_name = 'service'

    def get_object(self):
        return get_object_or_404(Service, id=self.kwargs['id'],
                                 is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        box_number = self.request.GET.get('box')
        date_str = self.request.GET.get('date')

        if box_number:
            box = get_object_or_404(Box,
                                    number=box_number,
                                    status=Box.StatusChoices.WORKING)
        else:
            box = Box.objects.filter(status=Box.StatusChoices.WORKING).first()

        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        slots = get_free_slots(self.object, date, box)

        context['available_slots'] = slots
        context['dates'] = [
            timezone.now().date() + timedelta(days=i) for i in range(7)
        ]
        context['boxes'] = self.object.boxes.filter(
            status=Box.StatusChoices.WORKING
            )
        context['selected_box'] = box
        context['selected_date'] = date

        return context


class CreateAppointmentView(FormView):
    form_class = AppointmentForm
    template_name = 'wash/create.html'

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, id=kwargs['id'],
                                         is_active=True)
        self.box = get_object_or_404(Box, pk=request.GET.get('box'))
        self.washer = get_object_or_404(Washer, pk=request.GET.get('washer'))
        time_str = request.GET.get('slot')
        date_str = request.GET.get('date')
        self.selected_slot = datetime.strptime(
            f'{date_str} {time_str}', '%Y-%m-%d %H:%M'
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context

    def form_valid(self, form):
        self.request.session['appointment_data'] = {
            'service_id': self.service.id,
            'box_number': self.box.number,
            'washer_id': self.washer.id,
            'slot': self.selected_slot.isoformat(),
            'client_name': form.cleaned_data['client_name'],
            'phone_number': str(form.cleaned_data['phone_number']),
        }
        return redirect('appointment_confirm', id=self.service.id)


class ConfirmAppointmentView(TemplateView):
    template_name = 'wash/confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.session.get('appointment_data')

        if not data:
            return redirect('index')

        context['service'] = get_object_or_404(Service, pk=data['service_id'])
        context['box'] = get_object_or_404(Box, pk=data['box_number'])
        context['washer'] = get_object_or_404(Washer, pk=data['washer_id'])
        context['slot_datetime'] = datetime.fromisoformat(data['slot'])
        context['client_name'] = data['client_name']
        context['phone_number'] = data['phone_number']

        return context

    def post(self, request, *args, **kwargs):
        data = request.session.get('appointment_data')

        if not data:
            return redirect('index')

        Appointment.objects.create(
            service_id=data['service_id'],
            box_id=data['box_number'],
            washer_id=data['washer_id'],
            date=datetime.fromisoformat(data['slot']),
            client_name=data['client_name'],
            phone_number=data['phone_number'],
            client=request.user if request.user.is_authenticated else None
        )

        del request.session['appointment_data']

        messages.success(request, 'Вы записаны!')
        if request.user.is_authenticated:
            return redirect('my_appointments')
        else:
            return redirect('index')


class AppointmentsView(LoginRequiredMixin, ListView):
    template_name = 'wash/appointments.html'
    context_object_name = 'appointments'
    paginate_by = 5

    def get_queryset(self):
        return self.request.user.appointments.order_by('-date')

    def handle_no_permission(self):
        messages.warning(
            self.request, 'Войдите в систему, чтобы просмотреть свои записи'
            )
        return redirect('login')


class MyWasherView(LoginRequiredMixin, ListView):
    template_name = 'wash/my_washer.html'
    model = Appointment

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_washer:
            messages.warning(request, 'Вы не являетесь мойщиком')
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        washer = self.request.user.washer_profile

        actual_appointments = washer.appointments.filter(
            date__gt=now
        ).order_by('date')

        filter_date_str = self.request.GET.get('filter_date')

        if filter_date_str:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            not_actual_all = washer.appointments.filter(
                date__lte=now,
                date__date=filter_date
            ).order_by('-date')
        else:
            not_actual_all = washer.appointments.filter(
                date__lte=now
            ).order_by('-date')

        paginator = Paginator(not_actual_all, 5)
        page_number = self.request.GET.get('page_history', 1)
        not_actual_appointments = paginator.get_page(page_number)

        context['actual_appointments'] = actual_appointments
        context['not_actual_appointments'] = not_actual_appointments
        context['washer'] = washer

        return context

    def handle_no_permission(self):
        messages.warning(self.request, 'Войдите в систему')
        return redirect('login')


class WasherEditView(LoginRequiredMixin, UpdateView):
    model = Washer
    form_class = WasherForm
    template_name = 'wash/washer_edit.html'
    success_url = reverse_lazy('my_washer')

    def get_object(self, queryset=None):
        return get_object_or_404(Washer, user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Данные обновлены!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, 'Исправьте ошибки в форме')
        return super().form_invalid(form)
