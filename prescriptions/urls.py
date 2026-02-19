from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CreatePrescriptionFromAIView,
    ParmacyViewSet,
    PrescriptionViewSet,
    UserAllMedicineViewSet,
    MarkMedicineTakenView,
    UserNotificationListView,
    MedicineStockView
)

router = DefaultRouter()
router.register(r'prescription', PrescriptionViewSet, basename='prescription')
router.register(r'pharmacy', ParmacyViewSet, basename='pharmacy')
router.register(r'medicines', UserAllMedicineViewSet, basename='user_medicines')
urlpatterns = [
    path('', include(router.urls)),
    path('prescription/from-ai/', CreatePrescriptionFromAIView.as_view(), name='prescription-from-ai'),
    # MediCine Stock
    path('medicine/mark-taken/<int:medicine_id>/', MarkMedicineTakenView.as_view(), name='medicine-mark-taken'),
    path('medicine/stock/<int:medicine_id>/', MedicineStockView.as_view(), name='medicine-stock'),
    # Notification view Api 
    path('notifications/', UserNotificationListView.as_view(), name='user-notifications'),
]
