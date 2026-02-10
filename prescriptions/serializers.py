from rest_framework import serializers
from .models import Prescription, Patient, Medicine, Medicine_Time, MedicalTest, pharmacy

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
    patient = PatientSerializer()
    medicines = MedicineSerializer(source="medicine_set", many=True)
    medical_tests = MedicalTestSerializer(source="medicaltest_set", many=True, required=False)

    class Meta:
        model = Prescription
        fields = [
            "id", "users", "doctor", "prescription_image", "next_appointment_date",
            "patient", "medicines", "medical_tests"
        ]

    def update(self, instance, validated_data):
        # Prescription main fields
        instance.doctor = validated_data.get('doctor', instance.doctor)
        instance.next_appointment_date = validated_data.get('next_appointment_date', instance.next_appointment_date)
        instance.save()

        # Patient update
        patient_data = validated_data.get('patient')
        if patient_data:
            Patient.objects.update_or_create(prescription=instance, defaults=patient_data)

        # Medicines update
        medicines_data = validated_data.get('medicine_set', [])
        for med in instance.medicine_set.all():
            for t in ["morning", "afternoon", "evening", "night"]:
                time_obj = getattr(med, t, None)
                if time_obj:
                    time_obj.delete()
            med.delete()

        for med in medicines_data:
            times = {}
            for t in ["morning", "afternoon", "evening", "night"]:
                time_data = med.pop(t, None)
                if time_data:
                    times[t] = Medicine_Time.objects.create(**time_data)
            med_obj = Medicine.objects.create(prescription=instance, **med)
            for t, obj in times.items():
                setattr(med_obj, t, obj)
            med_obj.save()

        # Medical tests update
        tests_data = validated_data.get('medicaltest_set', [])
        instance.medicaltest_set.all().delete()
        for test in tests_data:
            MedicalTest.objects.create(prescription=instance, **test)

        return instance

class PramcySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = pharmacy
        fields = [ 'pharmacy_name', 'Pharmacy_Address', 'website_link']
        
class UserMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'how_many_day', 'stock','prescription_id']