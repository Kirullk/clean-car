from rest_framework import serializers
from wash.models import Appointment, Box, Service, Washer, WasherCategory


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ('number',)


class WasherCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WasherCategory
        fields = ('name',)


class ServiceSerializer(serializers.ModelSerializer):
    boxes = BoxSerializer(many=True, read_only=True)
    washer_category = WasherCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = (
            'id',
            'name',
            'description',
            'average_time',
            'boxes',
            'price',
            'washer_category',
            'created_at'
        )
        read_only_fields = ('created_at',)


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ('number', 'status', 'max_height')


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class WasherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Washer
        fields = ('id', 'name', 'is_active', 'category', 'phone', 'shift_type')
