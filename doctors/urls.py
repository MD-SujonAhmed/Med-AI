from django.urls import include, path
from.views import  DoctorViewSet, DoctorNoteViewSet
from rest_framework.routers import DefaultRouter    

router = DefaultRouter()    
router.register('profile', DoctorViewSet, basename='doctors')

urlpatterns = [
    path('', include(router.urls)),

    # Notes endpoints
    path(
        'profile/<int:doctor_pk>/notes/',
        DoctorNoteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='doctor-notes'
    ),

    path(
        'profile/<int:doctor_pk>/notes/<int:pk>/',
        DoctorNoteViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='doctor-note-detail'
    ),
]
