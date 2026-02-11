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

    def get_queryset(self):
        return Prescription.objects.filter(users=self.request.user)

    def perform_create(self, serializer):
        serializer.save(users=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
class UserAllMedicineViewSet(viewsets.ModelViewSet):
    serializer_class = UserMedicineSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]
    http_method_names = ["get", "put", "patch","delete"]

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
