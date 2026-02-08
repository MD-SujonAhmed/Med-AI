from django.shortcuts import render

from doctors.models import Doctor, DoctorNote
from rest_framework.response import Response
from .serializers import DoctorNoteSerializer, DoctorSerializer
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
# Create your views here.

# class DoctorViewSet(viewsets.ModelViewSet):
#     queryset = Doctor.objects.all().prefetch_related('notes')
#     serializer_class = DoctorSerializer
#     # permission_classes = [permissions.IsAuthenticated]



class DoctorViewSet(viewsets.ModelViewSet):
    """
    Handles both listing all doctors and retrieving doctor details.
    - list: /doctors/profile/ → returns all doctors without notes (optional)
    - retrieve: /doctors/profile/{id}/ → returns doctor with notes and prescriptions
    """
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

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

    @action(detail=True, methods=['get', 'post'], url_path='notes')
    def doctor_notes(self, request, pk=None):
        """
        Optional endpoint to manage notes for a doctor:
        - GET: list notes
        - POST: create note
        """
        doctor = self.get_object()

        if request.method == 'GET':
            notes = doctor.notes.all()
            serializer = DoctorNoteSerializer(notes, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = DoctorNoteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(doctor=doctor)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)


class DoctorNotesByDoctor(APIView):
    def get(self, request, doctor_id):
        notes = DoctorNote.objects.filter(doctor_id=doctor_id)
        serializer = DoctorNoteSerializer(notes, many=True)
        return Response(serializer.data)

    def post(self, request, doctor_id):
        serializer = DoctorNoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(doctor_id=doctor_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
