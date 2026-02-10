from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParmacyViewSet, PrescriptionViewSet, UserAllMedicineViewSet

router = DefaultRouter()
router.register(r'', PrescriptionViewSet, basename='prescription')
router.register(r'pharmacy', ParmacyViewSet, basename='pharmacy')
router.register(r'medicines', UserAllMedicineViewSet, basename='user_medicines')

urlpatterns = [
    path('', include(router.urls)),
]
