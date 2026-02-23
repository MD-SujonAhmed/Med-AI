from rest_framework import serializers
from .models import Doctor, DoctorNote
from prescriptions.models import Prescription
from datetime import date

class DoctorNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorNote
        fields = ['id', 'note', 'date']

class DoctorSerializer(serializers.ModelSerializer):
    notes = DoctorNoteSerializer(many=True, read_only=True)
    prescriptions = serializers.SerializerMethodField()
    next_appointment_date = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id',
            'name',
            'sex',
            'specialization',
            'hospital_name',
            'designation',
            'doctor_email',
            'notes',
            'prescriptions',
            'next_appointment_date'
        ]

    def get_prescriptions(self, obj):
        # Return a list of prescription IDs for this doctor
        return list(Prescription.objects.filter(doctor=obj).values_list('id', flat=True))
    
    def get_next_appointment_date(self, obj):
        today = date.today()
        next_prescription = Prescription.objects.filter(
        doctor=obj,
        next_appointment_date__gte=today
        ).order_by('next_appointment_date').first()

        return [next_prescription.next_appointment_date.strftime('%Y-%m-%d')] if next_prescription else []

