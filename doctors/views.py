from django.shortcuts import render
from doctors.models import Doctor, DoctorNote
from rest_framework.response import Response
from .serializers import DoctorNoteSerializer, DoctorSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsNormalUser
# Create your views here.

class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_queryset(self):
        """
        Returns only doctors created by the logged-in user.
        """
        user = self.request.user
        return Doctor.objects.filter(user=user).prefetch_related('notes')
    
    def perform_create(self, serializer):
        # Automatically assign the logged-in user as the owner of the doctor
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """
        List all doctors without including notes (optional for performance)
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        # Remove notes from list view if you prefer
        for item in serializer.data:
            item.pop('notes', None)
            item.pop('prescriptions', None)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve doctor detail with notes and prescription IDs
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# doctors/views.py
class DoctorNoteViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorNoteSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_queryset(self):
        """
        Only notes of doctors owned by logged-in user
        """
        return DoctorNote.objects.filter(
            doctor__user=self.request.user
        )

    def perform_create(self, serializer):
        """
        Attach doctor safely from URL
        """
        doctor_id = self.kwargs.get("doctor_pk")
        try:
            doctor = Doctor.objects.get(
                id=doctor_id,
                user=self.request.user
            )
        except Doctor.DoesNotExist:
            raise PermissionError("Doctor not found or access denied")

        serializer.save(doctor=doctor)

    
    
