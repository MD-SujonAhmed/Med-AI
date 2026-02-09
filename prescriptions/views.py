from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import Prescription, Patient, Medicine, Medicine_Time, MedicalTest, pharmacy
from .serializers import PramcySerializer, PrescriptionSerializer, UserMedicineSerializer
from rest_framework.views import APIView


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    
    

    def get_queryset(self):
        user = self.request.user
        return Prescription.objects.filter(users=user) \
            .select_related('doctor', 'patient') \
            .prefetch_related('medicine_set', 'medicaltest_set')

def perform_create(self, serializer):
    data = self.request.data

    # ✅ 1. Save prescription first (patient ছাড়াই)
    prescription = serializer.save(users=self.request.user)

    # ✅ 2. Create patient with prescription link
    patient_data = data.get("patient")
    patient_obj = Patient.objects.create(
        prescription=prescription,
        name=patient_data['name'],
        age=patient_data['age'],
        sex=patient_data.get('sex', ''),
        health_issues=patient_data.get('health_issues', '')
    )

    # 3. Save medicines
    medicines = data.get("medicines", [])
    for med in medicines:
        times = {}
        for t in ["morning", "afternoon", "evening", "night"]:
            time_data = med.pop(t, None)
            if time_data:
                times[t] = Medicine_Time.objects.create(**time_data)

        med_obj = Medicine.objects.create(prescription=prescription, **med)
        for t, obj in times.items():
            setattr(med_obj, t, obj)
        med_obj.save()

    # 4. Save medical tests
    tests = data.get("medical_tests", [])
    for test in tests:
        MedicalTest.objects.create(prescription=prescription, **test)
    def perform_update(self, serializer):
        data = self.request.data
        prescription = self.get_object()

        # Update patient
        patient_data = data.get("patient")
        if patient_data:
            for attr, value in patient_data.items():
                setattr(prescription.patient, attr, value)
            prescription.patient.save()

        # Update prescription fields
        serializer.save()

        # Update medicines (delete old & create new)
        prescription.medicine_set.all().delete()
        medicines = data.get("medicines", [])
        for med in medicines:
            times = {}
            for t in ["morning", "afternoon", "evening", "night"]:
                time_data = med.pop(t, None)
                if time_data:
                    times[t] = Medicine_Time.objects.create(**time_data)

            med_obj = Medicine.objects.create(prescription=prescription, **med)
            for t, obj in times.items():
                setattr(med_obj, t, obj)
            med_obj.save()

        # Update medical tests (delete old & create new)
        prescription.medicaltest_set.all().delete()
        tests = data.get("medical_tests", [])
        for test in tests:
            MedicalTest.objects.create(prescription=prescription, **test)




class UserAllMedicineViewSet(viewsets.ModelViewSet):
    serializer_class = UserMedicineSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "patch"]

    def get_queryset(self):
        return Medicine.objects.filter(
            prescription__users=self.request.user
        ).select_related("prescription")


class ParmacyViewSet(viewsets.ModelViewSet):
    queryset = pharmacy.objects.all()
    serializer_class = PramcySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # automatically set the logged-in user
        serializer.save(user=self.request.user)
    
    
