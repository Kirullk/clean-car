from django.contrib import admin

from .models import (
    Box, WasherCategory, Service, WorkingHours,
    ShiftType, Washer, Appointment
)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('number', 'status', 'max_height')
    list_filter = ('status',)
    search_fields = ('number',)
    list_editable = ('status',)
    ordering = ('number',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'status', 'max_height')
        }),
    )


@admin.register(WasherCategory)
class WasherCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display')
    search_fields = ('name',)

    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Название'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'average_time', 'is_active', 'created_at')
    list_filter = ('is_active', 'boxes', 'washer_category')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_active')
    filter_horizontal = ('boxes', 'washer_category')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name', 'description', 'is_active', 'price', 'average_time'
                )
        }),
        ('Связи', {
            'fields': ('boxes', 'washer_category')
        }),
        ('Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('day', 'open_time', 'close_time', 'is_working')
    list_filter = ('is_working',)
    list_editable = ('open_time', 'close_time', 'is_working')

    fieldsets = (
        (None, {
            'fields': ('day', 'open_time', 'close_time', 'is_working')
        }),
    )


@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display')
    search_fields = ('name',)

    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Название'


@admin.register(Washer)
class WasherAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'is_active', 'shift_type', 'phone')
    list_filter = ('is_active', 'category', 'shift_type')
    search_fields = ('name', 'user__username', 'phone')
    list_editable = ('is_active', 'category')
    readonly_fields = ('hire_date',)
    raw_id_fields = ('user',)

    fieldsets = (
        ('Личная информация', {
            'fields': ('user', 'name', 'phone', 'category', 'shift_type')
        }),
        ('Статус', {
            'fields': ('is_active', 'hire_date')
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'phone_number', 'service', 'date', 'box', 'washer', 'created_at')
    list_filter = ('service', 'box', 'washer', 'date')
    search_fields = ('client_name', 'phone_number', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('client', 'washer')

    fieldsets = (
        ('Клиент', {
            'fields': ('client', 'client_name', 'phone_number')
        }),
        ('Запись', {
            'fields': ('service', 'date', 'box', 'washer')
        }),
        ('Дополнительно', {
            'fields': ('comment', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # При редактировании
            return self.readonly_fields + ('client', 'service', 'date', 'box', 'washer')
        return self.readonly_fields
