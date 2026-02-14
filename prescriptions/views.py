from requests import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from .models import Prescription, Patient, Medicine, Medicine_Time, MedicalTest, pharmacy
from .serializers import PrescriptionSerializer, PramcySerializer, UserMedicineSerializer
from users.permissions import IsNormalUser, IsAdminOrSuperUser
from rest_framework.views import APIView
from rest_framework import status

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



class CreatePrescriptionFromAIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data.get("data")
        if not payload:
            return Response({"detail": "data is required"}, status=400)

        # Prescription create (user always from JWT)
        doctor_id = payload.get("doctor")  # may be null
        prescription = Prescription.objects.create(
            users=request.user,
            doctor_id=doctor_id if doctor_id else None,
        )

        # Patient create
        p = payload.get("patient") or {}
        Patient.objects.create(
            prescription=prescription,
            name=p.get("name", "") or "",
            age=p.get("age") or 0,
            sex=p.get("sex", "") or "",
            health_issues=p.get("health_issues", "") or "",
        )

        # Medicines create (IGNORE how_many_time)
        meds = payload.get("medicines") or []
        for m in meds:
            Medicine.objects.create(
                prescription=prescription,
                name=m.get("name", "") or "",
                how_many_day=m.get("how_many_day") or 0,
                stock=m.get("stock") or 0,
                # morning/afternoon/evening/night will stay NULL
            )

        return Response(
            {"success": True, "prescription_id": prescription.id},
            status=status.HTTP_201_CREATED
        )