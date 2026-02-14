from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreatePrescriptionFromAIView, ParmacyViewSet, PrescriptionViewSet, UserAllMedicineViewSet

router = DefaultRouter()
router.register(r'prescription', PrescriptionViewSet, basename='prescription')
router.register(r'pharmacy', ParmacyViewSet, basename='pharmacy')
router.register(r'medicines', UserAllMedicineViewSet, basename='user_medicines')

urlpatterns = [
    path('', include(router.urls)),
    path('prescription/from-ai/', CreatePrescriptionFromAIView.as_view(), name='prescription-from-ai'),
]
