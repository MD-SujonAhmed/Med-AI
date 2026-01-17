from django.shortcuts import render
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework import permissions
from .serializers import SingUpSerializer
from.models import Users
# Create your views here.

class SignUpView(APIView):
    
    def post(self, request):
        serializer=SingUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"User SignUp successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)