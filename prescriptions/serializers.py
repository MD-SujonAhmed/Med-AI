from rest_framework import serializers
from .models import Prescription

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'user', 'image', 'uploaded_at']
        read_only_fields = ['id', 'user', 'uploaded_at']