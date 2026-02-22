from rest_framework.response import Response  
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from .models import Prescription, Patient, Medicine, pharmacy, NotificationLog
from .serializers import (
    PrescriptionSerializer, 
    PramcySerializer, 
    UserMedicineSerializer,
    NotificationLogSerializer,
    MedicineStockSerializer
)
from users.permissions import IsNormalUser, IsAdminOrSuperUser
from prescriptions.tasks import send_push_notification


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

        doctor_id = payload.get("doctor")
        prescription = Prescription.objects.create(
            users=request.user,
            doctor_id=doctor_id if doctor_id else None,
        )

        p = payload.get("patient") or {}
        Patient.objects.create(
            prescription=prescription,
            name=p.get("name", "") or "",
            age=p.get("age") or 0,
            sex=p.get("sex", "") or "",
            health_issues=p.get("health_issues", "") or "",
        )

        meds = payload.get("medicines") or []
        for m in meds:
            Medicine.objects.create(
                prescription=prescription,
                name=m.get("name", "") or "",
                how_many_day=m.get("how_many_day") or 0,
                stock=m.get("stock") or 0,
            )

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
    permission_classes = [IsAuthenticated, IsNormalUser]

    def post(self, request, medicine_id):
        try:
            medicine = Medicine.objects.get(
                id=medicine_id,
                prescription__users=request.user
            )
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)

        if medicine.stock <= 0:
            return Response({
                "message": "Stock is empty! Please buy more.",
                "current_stock": 0
            }, status=400)

        medicine.stock -= 1
        medicine.save()

        if medicine.stock <= 3:
            if medicine.stock == 0:
                msg = f"🚨 {medicine.name} is out of stock! Please buy now."
            else:
                msg = f"⚠️ {medicine.name} has only {medicine.stock} day(s) left!"

            send_push_notification(
                medicine.prescription.users,
                "Low Stock Alert",
                msg,
                notification_type='low_stock_alert',
                medicine=medicine
            )

        return Response({
            "message": "Medicine marked as taken!",
            "medicine": medicine.name,
            "remaining_stock": medicine.stock
        })


class MedicineStockView(APIView):
    permission_classes = [IsAuthenticated, IsNormalUser]

    def post(self, request, medicine_id):
        serializer = MedicineStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            medicine = Medicine.objects.get(
                id=medicine_id,
                prescription__users=request.user
            )
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)

        stock = serializer.validated_data["stock"]
        medicine.stock += stock
        medicine.save()

        return Response({
            "message": f"{stock} stock added successfully",
            "medicine": medicine.name,
            "current_stock": medicine.stock
        })


class UserNotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get(self, request):
        # ✅ শুধু আজকের notification
        today = timezone.now().date()
        logs = NotificationLog.objects.filter(
            user=request.user,
            sent_at__date=today
        ).order_by('-sent_at')
        serializer = NotificationLogSerializer(logs, many=True)
        return Response(serializer.data, status=200)

    def delete(self, request):
        # ✅ সব notification delete
        NotificationLog.objects.filter(user=request.user).delete()
        return Response({"message": "All notifications deleted!"}, status=200)


class UserNotificationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsNormalUser]

    def delete(self, request, notification_id):
        # ✅ Specific notification delete
        try:
            log = NotificationLog.objects.get(
                id=notification_id,
                user=request.user
            )
            log.delete()
            return Response({"message": "Notification deleted!"}, status=200)
        except NotificationLog.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

    def patch(self, request, notification_id):
        # ✅ Read mark করো
        try:
            log = NotificationLog.objects.get(
                id=notification_id,
                user=request.user
            )
            log.is_read = True
            log.save()
            return Response({"message": "Marked as read!"}, status=200)
        except NotificationLog.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


class AdminNotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        # ✅ সব notification + unread count
        logs = NotificationLog.objects.all().order_by('-sent_at')[:50]
        unread_count = NotificationLog.objects.filter(is_read=False).count()
        serializer = NotificationLogSerializer(logs, many=True)
        return Response({
            "unread_count": unread_count,
            "notifications": serializer.data
        }, status=200)