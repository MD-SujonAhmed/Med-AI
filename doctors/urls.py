from django.urls import include, path
from.views import DoctorNotesByDoctor,  DoctorViewSet
from rest_framework.routers import DefaultRouter    

router = DefaultRouter()    
router.register('profile', DoctorViewSet, basename='doctors')
# router.register('notes', DoctorNoteView, basename='doctor_notes')

urlpatterns = [
    path('', include(router.urls)),
]
