import json

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from .models import Prescription, Patient, Medicine, MedicalTest
from .serializers import PrescriptionSerializer
from users.models import Users
from doctors.models import Doctor


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing prescriptions with nested patient, medicines, and medical tests
    """
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """
        Optionally filter prescriptions by user
        """
        queryset = Prescription.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        doctor_id = self.request.query_params.get('doctor_id', None)
        
        if user_id:
            queryset = queryset.filter(users__id=user_id)
        
        if doctor_id:
            queryset = queryset.filter(doctor__id=doctor_id)
        
        return queryset.select_related('users', 'doctor', 'patient').prefetch_related('medicine_set', 'medicaltest_set')
    
    def create(self, request, *args, **kwargs):
        """
        Create a new prescription with nested data
        """
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        
        if serializer.is_valid():
            prescription = serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update prescription with nested data
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            prescription = serializer.save()
            return Response(serializer.data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def my_prescriptions(self, request):
        """
        Get all prescriptions for the current authenticated user
        """
        prescriptions = Prescription.objects.filter(users=request.user).select_related('users', 'doctor', 'patient').prefetch_related('medicine_set', 'medicaltest_set')
        serializer = self.get_serializer(prescriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def medicines(self, request, pk=None):
        """
        Get all medicines for a specific prescription
        """
        prescription = self.get_object()
        medicines = prescription.medicine_set.all()
        from .serializers import MedicineSerializer
        serializer = MedicineSerializer(medicines, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def medical_tests(self, request, pk=None):
        """
        Get all medical tests for a specific prescription
        """
        prescription = self.get_object()
        tests = prescription.medicaltest_set.all()
        from .serializers import MedicalTestSerializer
        serializer = MedicalTestSerializer(tests, many=True)
        return Response(serializer.data)