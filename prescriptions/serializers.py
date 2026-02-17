from rest_framework import serializers
from .models import Prescription, Patient, Medicine, Medicine_Time, MedicalTest, pharmacy,NotificationLog

class MedicineTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine_Time
        fields = ["time", "before_meal", "after_meal"]

class MedicineSerializer(serializers.ModelSerializer):
    morning = MedicineTimeSerializer(required=False, allow_null=True)
    afternoon = MedicineTimeSerializer(required=False, allow_null=True)
    evening = MedicineTimeSerializer(required=False, allow_null=True)
    night = MedicineTimeSerializer(required=False, allow_null=True)

    class Meta:
        model = Medicine
        fields = ["id", "name", "how_many_day", "stock", "morning", "afternoon", "evening", "night"]

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["id", "name", "age", "sex", "health_issues"]

class MedicalTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalTest
        fields = ["id", "test_name"]

class PrescriptionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(required=False)
    medicines = MedicineSerializer(
        source="medicine_set",
        many=True,
        required=False
    )
    medical_tests = MedicalTestSerializer(
        source="medicaltest_set",
        many=True,
        required=False
    )

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
        ]
        read_only_fields = ["users"]

    # ✅ IMPORTANT: Explicit update method
    def update(self, instance, validated_data):

        # 🔥 REMOVE nested data FIRST
        patient_data = validated_data.pop("patient", None)
        medicines_data = validated_data.pop("medicine_set", [])
        tests_data = validated_data.pop("medicaltest_set", [])

        # Update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update patient
        if patient_data:
            Patient.objects.update_or_create(
                prescription=instance,
                defaults=patient_data
            )

        # Delete old medicines
        instance.medicine_set.all().delete()

        # Create medicines again
        for med in medicines_data:
            times = {}

            for t in ["morning", "afternoon", "evening", "night"]:
                time_data = med.pop(t, None)
                if time_data:
                    times[t] = Medicine_Time.objects.create(**time_data)

            med_obj = Medicine.objects.create(
                prescription=instance,
                **med
            )

            for t, obj in times.items():
                setattr(med_obj, t, obj)

            med_obj.save()

        # Update tests
        instance.medicaltest_set.all().delete()

        for test in tests_data:
            MedicalTest.objects.create(
                prescription=instance,
                **test
            )

        return instance

    def create(self, validated_data):

        patient_data = validated_data.pop("patient", None)
        medicines_data = validated_data.pop("medicine_set", [])
        tests_data = validated_data.pop("medicaltest_set", [])
    
        # Create Prescription
        prescription = Prescription.objects.create(**validated_data)
    
        # Create Patient
        if patient_data:
            Patient.objects.create(
                prescription=prescription,
                **patient_data
            )
    
        # Create Medicines
        for med in medicines_data:
            times = {}
    
            for t in ["morning", "afternoon", "evening", "night"]:
                time_data = med.pop(t, None)
                if time_data:
                    times[t] = Medicine_Time.objects.create(**time_data)
    
            med_obj = Medicine.objects.create(
                prescription=prescription,
                **med
            )
    
            for t, obj in times.items():
                setattr(med_obj, t, obj)
    
            med_obj.save()
    
        # Create Medical Tests
        for test in tests_data:
            MedicalTest.objects.create(
                prescription=prescription,
                **test
            )
    
        return prescription

class PramcySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = pharmacy
        fields = [ 'pharmacy_name', 'Pharmacy_Address', 'website_link']
        

class UserMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'how_many_day', 'stock','prescription_id']
        
 
class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'notification_type',
            'title',
            'body',
            'is_sent',
            'sent_at',
            'medicine',
        ]