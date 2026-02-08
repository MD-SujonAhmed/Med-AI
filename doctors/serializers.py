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
        ]

    def get_prescriptions(self, obj):
        # Return a list of prescription IDs for this doctor
        return list(Prescription.objects.filter(doctor=obj).values_list('id', flat=True))
