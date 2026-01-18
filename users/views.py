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
from .utils.email import send_otp_email
# Create your views here.

class SignUpView(APIView):
    
    def post(self, request):
        serializer = SingUpSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save(is_active=False)

            otp = generate_otp()               # ✅ generate ONCE
            store_otp(user.email, otp)         # ✅ store same OTP
            send_otp_email(user.email, otp, 'signup')  # ✅ send same OTP

            return Response(
                {"message": "Signup successful. OTP sent to email."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class RequestOTPView(APIView):  # why this view is needed?
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
            {"message": "OTP sent to your email. Please verify to complete signup."},
            status=status.HTTP_200_OK
        )

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {"error": "email and otp are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not verify_otp(email, otp):
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Users.objects.get(email=email)
            user.is_active = True
            user.save()
        except Users.DoesNotExist:
            return Response(
                {"error": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"message": "Signup successful. Account activated."},
            status=status.HTTP_200_OK
        )

