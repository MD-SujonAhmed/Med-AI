from rest_framework.response import Response  # ✅ সঠিক import
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Prescription, Patient, Medicine, pharmacy,NotificationLog
from .serializers import PrescriptionSerializer, PramcySerializer, UserMedicineSerializer,NotificationLogSerializer
from users.permissions import IsNormalUser
from prescriptions.tasks import send_medicine_reminder, send_push_notification

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


class CreatePrescriptionFromAIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data.get("data")
        if not payload:
            return Response({"detail": "data is required"}, status=400)

        # Prescription create
        doctor_id = payload.get("doctor")
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

        # Medicines create
        meds = payload.get("medicines") or []
        for m in meds:
            med = Medicine.objects.create(
                prescription=prescription,
                name=m.get("name", "") or "",
                how_many_day=m.get("how_many_day") or 0,
                stock=m.get("stock") or 0,
            )
            # ✅ Schedule reminders for this medicine
            schedule_medicine_reminders(med)

        return Response(
            {"success": True, "prescription_id": prescription.id},
            status=status.HTTP_201_CREATED
        )


class UserAllMedicineViewSet(viewsets.ModelViewSet):
    serializer_class = UserMedicineSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]
    http_method_names = ["get", "put", "patch", "delete"]

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

class MarkMedicineTakenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, medicine_id):
        """
        Mark medicine as taken and decrease stock
        """
        try:
            medicine = Medicine.objects.select_related('prescription__users').get(
                id=medicine_id,
                prescription__users=request.user
            )
        except Medicine.DoesNotExist:
            return Response(
                {'error': 'Medicine not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        slot = request.data.get('slot')  # 'morning', 'afternoon', 'evening', 'night'
        
        if not slot:
            return Response(
                {'error': 'Slot is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decrease stock
        if medicine.stock > 0:
            medicine.stock -= 1
            medicine.save()
            
            # Check if low stock (≤3 days)
            if medicine.stock <= 3:
                from .tasks import send_push_notification
                
                if medicine.stock == 0:
                    msg = f"⚠️ {medicine.name} is out of stock!"
                else:
                    msg = f"⚠️ {medicine.name} has {medicine.stock} day(s) left."
                
                send_push_notification(
                    medicine.prescription.users,
                    "Low Stock Alert",
                    msg,
                    notification_type='low_stock_alert',
                    medicine=medicine
                )
            
            return Response({
                'success': True,
                'message': f'{medicine.name} marked as taken',
                'remaining_stock': medicine.stock
            })
        else:
            return Response(
                {'error': 'Medicine is out of stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserNotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = NotificationLog.objects.filter(user=request.user).order_by('-sent_at')
        serializer = NotificationLogSerializer(logs, many=True)
        return Response(serializer.data, status=200)