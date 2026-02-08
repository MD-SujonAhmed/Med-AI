import json
from rest_framework import serializers

from .models import Prescription, Patient, Medicine, MedicalTest, Medicine_Time


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["name", "age", "sex", "health_issues"]


class MedicineTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine_Time
        fields = ["time", "before_meal", "after_meal"]


class MedicineSerializer(serializers.ModelSerializer):
    morning = MedicineTimeSerializer(read_only=True)
    afternoon = MedicineTimeSerializer(read_only=True)
    evening = MedicineTimeSerializer(read_only=True)
    night = MedicineTimeSerializer(read_only=True)

    class Meta:
        model = Medicine
        fields = [
            "name",
            "how_many_day",
            "stock",
            "morning",
            "afternoon",
            "evening",
            "night",
            "created_at",
            "updated_at",
        ]


class MedicalTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalTest
        fields = ["test_name"]


class PrescriptionSerializer(serializers.ModelSerializer):
    patient = serializers.CharField(write_only=True)
    medicines = serializers.CharField(write_only=True, required=False)
    medical_tests = serializers.CharField(write_only=True, required=False)

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
            "doctor_name",
        ]

    def _create_time_slot(self, slot_data):
        """
        slot_data example:
        { "time": "08:00:00", "before_meal": true, "after_meal": false }
        """
        if not slot_data:
            return None
        return Medicine_Time.objects.create(
            time=slot_data.get("time"),
            before_meal=slot_data.get("before_meal", False),
            after_meal=slot_data.get("after_meal", False),
        )

    def create(self, validated_data):
        patient_raw = validated_data.pop("patient")
        medicines_raw = validated_data.pop("medicines", "[]")
        medical_tests_raw = validated_data.pop("medical_tests", "[]")

        try:
            patient_data = json.loads(patient_raw)
            medicines_data = json.loads(medicines_raw)
            medical_tests_data = json.loads(medical_tests_raw)
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format")

        prescription = Prescription.objects.create(**validated_data)

        Patient.objects.create(prescription=prescription, **patient_data)

        # ✅ create medicines with new slots
        for med in medicines_data:
            morning_obj = self._create_time_slot(med.get("morning"))
            afternoon_obj = self._create_time_slot(med.get("afternoon"))
            evening_obj = self._create_time_slot(med.get("evening"))
            night_obj = self._create_time_slot(med.get("night"))

            Medicine.objects.create(
                prescription=prescription,
                name=med.get("name"),
                how_many_day=med.get("how_many_day"),
                stock=med.get("stock", 0),
                morning=morning_obj,
                afternoon=afternoon_obj,
                evening=evening_obj,
                night=night_obj,
            )

        for test in medical_tests_data:
            MedicalTest.objects.create(prescription=prescription, **test)

        return prescription

    def update(self, instance, validated_data):
        patient_raw = validated_data.pop("patient", None)
        medicines_raw = validated_data.pop("medicines", None)
        medical_tests_raw = validated_data.pop("medical_tests", None)

        # update prescription fields
        instance.users = validated_data.get("users", instance.users)
        instance.doctor = validated_data.get("doctor", instance.doctor)
        instance.prescription_image = validated_data.get("prescription_image", instance.prescription_image)
        instance.next_appointment_date = validated_data.get("next_appointment_date", instance.next_appointment_date)
        instance.save()

        # patient update
        if patient_raw:
            try:
                patient_data = json.loads(patient_raw) if isinstance(patient_raw, str) else patient_raw
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid patient JSON format")

            patient = getattr(instance, "patient", None)
            if patient:
                patient.name = patient_data.get("name", patient.name)
                patient.age = patient_data.get("age", patient.age)
                patient.sex = patient_data.get("sex", patient.sex)
                patient.health_issues = patient_data.get("health_issues", patient.health_issues)
                patient.save()

        # medicines update (simple way: delete and recreate)
        if medicines_raw is not None:
            try:
                medicines_data = json.loads(medicines_raw) if isinstance(medicines_raw, str) else medicines_raw
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid medicines JSON format")

            # delete old time slots to avoid orphan rows
            for old_med in instance.medicine_set.all():
                for slot in [old_med.morning, old_med.afternoon, old_med.evening, old_med.night]:
                    if slot:
                        slot.delete()
            instance.medicine_set.all().delete()

            for med in medicines_data:
                morning_obj = self._create_time_slot(med.get("morning"))
                afternoon_obj = self._create_time_slot(med.get("afternoon"))
                evening_obj = self._create_time_slot(med.get("evening"))
                night_obj = self._create_time_slot(med.get("night"))

                Medicine.objects.create(
                    prescription=instance,
                    name=med.get("name"),
                    how_many_day=med.get("how_many_day"),
                    stock=med.get("stock", 0),
                    morning=morning_obj,
                    afternoon=afternoon_obj,
                    evening=evening_obj,
                    night=night_obj,
                )

        # medical tests update
        if medical_tests_raw is not None:
            try:
                medical_tests_data = json.loads(medical_tests_raw) if isinstance(medical_tests_raw, str) else medical_tests_raw
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid medical_tests JSON format")

            instance.medicaltest_set.all().delete()
            for test in medical_tests_data:
                MedicalTest.objects.create(prescription=instance, **test)

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            representation["patient"] = PatientSerializer(instance.patient).data
        except Patient.DoesNotExist:
            representation["patient"] = None

        representation["medicines"] = MedicineSerializer(instance.medicine_set.all(), many=True).data
        representation["medical_tests"] = MedicalTestSerializer(instance.medicaltest_set.all(), many=True).data

        return representation
    
    
    
