from django.shortcuts import render
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework import permissions
from .serializers import SingUpSerializer
from.models import Users
from .utils.otp import generate_otp,store_otp,verify_otp
from .utils.email import send_otp_email, send_otp_via_email
# Create your views here.

class SignUpView(APIView):
    
    def post(self, request):
        serializer=SingUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"User SignUp successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class RequestOTPView(APIView):
    def post(self,request):
        email=request.data.get("email")
        purpose=request.data.get("purpose")  # 'signup' or 'password_reset'
        
        if not email or not purpose:
            return Response(
                {"error": "email and purpose are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = generate_otp()
        store_otp(email, otp)
        send_otp_email(email, otp, purpose)

        return Response(
            {"message": "OTP sent successfully"},
            status=status.HTTP_200_OK
        )

class VerifyOTPView(APIView):
    def post(self, request):
        email=request.data.get("email")
        otp=request.data.get("otp")
        purpose=request.data.get("purpose")  # 'signup' or 'password_reset'
        
        if not email or not otp or not purpose:
            return Response(
                {"error": "email, otp and purpose are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if verify_otp(email, otp):
            return Response(
                {"message": "OTP verified successfully"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if purpose == "signup":
            
            user