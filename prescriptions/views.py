from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from .models import Prescription, Patient, Medicine, Medicine_Time, MedicalTest, pharmacy
from .serializers import PrescriptionSerializer, PramcySerializer, UserMedicineSerializer
from users.permissions import IsNormalUser, IsAdminOrSuperUser

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Prescription.objects.filter(users=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        data = self.request.data
        prescription = serializer.save(users=self.request.user)

        # Patient
        patient_data = data.get("patient")
        if patient_data:
            Patient.objects.create(
                prescription=prescription,
                name=patient_data["name"],
                age=patient_data["age"],
                sex=patient_data.get("sex", ""),
                health_issues=patient_data.get("health_issues", "")
            )

        # Medicines
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

        # Medical Tests
        tests = data.get("medical_tests", [])
        for test in tests:
            MedicalTest.objects.create(prescription=prescription, **test)

    @transaction.atomic
    def perform_update(self, serializer):
        data = self.request.data
        prescription = serializer.save()

        # Patient update
        patient_data = data.get("patient")
        if patient_data:
            Patient.objects.update_or_create(
                prescription=prescription,
                defaults=patient_data
            )

        # Medicines update
        medicines_data = data.get("medicines", [])
        # Delete old medicines and times
        for med in prescription.medicine_set.all():
            for t in ["morning", "afternoon", "evening", "night"]:
                time_obj = getattr(med, t, None)
                if time_obj is not None:
                    time_obj.delete()
            med.delete()

        # Create new medicines
        for med in medicines_data:
            times = {}
            for t in ["morning", "afternoon", "evening", "night"]:
                time_data = med.pop(t, None)
                if time_data:
                    times[t] = Medicine_Time.objects.create(**time_data)
            med_obj = Medicine.objects.create(prescription=prescription, **med)
            for t, obj in times.items():
                setattr(med_obj, t, obj)
            med_obj.save()

        # Medical Tests update
        tests_data = data.get("medical_tests", [])
        prescription.medicaltest_set.all().delete()
        for test in tests_data:
            MedicalTest.objects.create(prescription=prescription, **test)


class UserAllMedicineViewSet(viewsets.ModelViewSet):
    serializer_class = UserMedicineSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]
    http_method_names = ["get", "put", "patch"]

    def get_queryset(self):
        return Medicine.objects.filter(
            prescription__users=self.request.user
        ).select_related("prescription")


class ParmacyViewSet(viewsets.ModelViewSet):
    queryset = pharmacy.objects.all()
    serializer_class = PramcySerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
