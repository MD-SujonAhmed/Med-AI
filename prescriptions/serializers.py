from rest_framework import serializers
from .models import Prescription, Patient, Medicine, Medicine_Time, MedicalTest


class MedicineTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine_Time
        fields = ["time", "before_meal", "after_meal"]


class MedicineSerializer(serializers.ModelSerializer):
    morning = MedicineTimeSerializer(required=False, read_only=True)
    afternoon = MedicineTimeSerializer(required=False, read_only=True)
    evening = MedicineTimeSerializer(required=False, read_only=True)
    night = MedicineTimeSerializer(required=False, read_only=True)

    class Meta:
        model = Medicine
        fields = ["name", "how_many_day", "stock", "morning", "afternoon", "evening", "night"]


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["name", "age", "sex", "health_issues"]


class MedicalTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalTest
        fields = ["test_name"]


class PrescriptionSerializer(serializers.ModelSerializer):
    # ✅ সব nested fields read_only করো
    patient = PatientSerializer(read_only=True)
    medicines = MedicineSerializer(source='medicine_set', many=True, read_only=True)
    medical_tests = MedicalTestSerializer(source='medicaltest_set', many=True, required=False, read_only=True)

    user_name = serializers.CharField(source="users.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "users",
            "doctor",
            "prescription_image",
            "next_appointment_date",
            "patient",
            "medicines",
            "medical_tests",
            "user_name",
            "doctor_name"
        ]