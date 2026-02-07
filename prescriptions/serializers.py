import json
from rest_framework import serializers

from .models import Prescription, Patient, Medicine, MedicalTest
from users.models import UserProfile, Users
from doctors.models import Doctor


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'sex', 'health_issues']


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            'name',
            'how_many_time',
            'how_many_day',
            'created_at',
            'updated_at',
            'before_meal',
            'after_meal',
            'stock'
        ]


class MedicalTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalTest
        fields = ['test_name']


class PrescriptionSerializer(serializers.ModelSerializer):
    patient = serializers.CharField(write_only=True)
    medicines = serializers.CharField(write_only=True, required=False)
    medical_tests = serializers.CharField(write_only=True, required=False)

    # Read-only display fields
    user_name = serializers.CharField(
        source='users.full_name',
        read_only=True
    )
    doctor_name = serializers.CharField(
        source='doctor.name',
        read_only=True
    )

    class Meta:
        model = Prescription
        fields = [
            'id',
            'users',
            'doctor',
            'prescription_image',
            'next_appointment_date',
            'patient',
            'medicines',
            'medical_tests',
            'user_name',
            'doctor_name'
        ]

    def create(self, validated_data):
        """
        Create a prescription with:
        - patient (JSON)
        - medicines (JSON)
        - medical_tests (JSON)
        """

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

        Patient.objects.create(
            prescription=prescription,
            **patient_data
        )

        for med in medicines_data:
            Medicine.objects.create(
                prescription=prescription,
                **med
            )

        for test in medical_tests_data:
            MedicalTest.objects.create(
                prescription=prescription,
                **test
            )

        return prescription

    def update(self, instance, validated_data):
        patient_data = validated_data.pop('patient', None)
        medicines_data = validated_data.pop('medicines', None)
        medical_tests_data = validated_data.pop('medical_tests', None)

        instance.users = validated_data.get('users', instance.users)
        instance.doctor = validated_data.get('doctor', instance.doctor)
        instance.prescription_image = validated_data.get(
            'prescription_image',
            instance.prescription_image
        )
        instance.next_appointment_date = validated_data.get(
            'next_appointment_date',
            instance.next_appointment_date
        )
        instance.save()

        if patient_data:
            patient = instance.patient
            patient.name = patient_data.get('name', patient.name)
            patient.age = patient_data.get('age', patient.age)
            patient.sex = patient_data.get('sex', patient.sex)
            patient.health_issues = patient_data.get(
                'health_issues',
                patient.health_issues
            )
            patient.save()

        if medicines_data is not None:
            instance.medicine_set.all().delete()
            for med in medicines_data:
                Medicine.objects.create(
                    prescription=instance,
                    **med
                )

        if medical_tests_data is not None:
            instance.medicaltest_set.all().delete()
            for test in medical_tests_data:
                MedicalTest.objects.create(
                    prescription=instance,
                    **test
                )

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            patient = instance.patient
            representation['patient'] = PatientSerializer(patient).data
        except Patient.DoesNotExist:
            representation['patient'] = None

        representation['medicines'] = MedicineSerializer(
            instance.medicine_set.all(),
            many=True
        ).data

        representation['medical_tests'] = MedicalTestSerializer(
            instance.medicaltest_set.all(),
            many=True
        ).data

        return representation
