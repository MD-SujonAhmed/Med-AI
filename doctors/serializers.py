from rest_framework import serializers
from .models import Doctor, DoctorNote
from prescriptions.models import Prescription

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
        # Get all prescriptions of this doctor with dates
        dates = Prescription.objects.filter(
            doctor=obj, 
            next_appointment_date__isnull=False
        ).values_list('next_appointment_date', flat=True)

        # Convert dates to string format YYYY-MM-DD
        date_strings = [d.strftime('%Y-%m-%d') for d in dates]

        # Return as a JSON array (even if empty)
        return date_strings

