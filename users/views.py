from datetime import timedelta
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from doctors.models import Doctor
from prescriptions.models import Medicine, Prescription
from .serializers import (
    AdminUserListSerializer,
    ChangePasswordSerializer,
    DeactivateAccountSerializer,
    DoctorListSerializer,
    SingUpSerializer,
    OtpVerificationSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    AdminProfileSerializer,
    AdminChangePasswordSerializer,
    LogoutSerializer,
    DeleteAccountSerializer,
   AdminDashboardSerializer
)
from .models import Users, UserProfile
from .utils.otp import generate_otp, store_otp, verify_otp, is_password_reset_verified
from .utils.email import send_otp_email
from .permissions import IsAdminOrSuperUser,IsNormalUser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncMonth
from django.db.models import Count
from prescriptions.serializers  import PramcySerializer
from prescriptions.models  import pharmacy


# -----------------------------
#  User Registration / Signup
# -----------------------------
@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(APIView):
    """
    User Sign Up
    - Save user as inactive
    - Generate OTP
    - Send OTP email
    """
    def post(self, request):
        serializer = SingUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            otp = generate_otp()
            store_otp(user.email, otp, purpose="signup")
            send_otp_email(user.email, otp, "signup")
            return Response(
                {"message": f"OTP sent to {user.email} for account verification."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
#  OTP Management
# -----------------------------
    """Request OTP for signup or password reset"""
class RequestOTPView(APIView):
        def post(self, request):
            email = request.data.get("email")
            purpose = request.data.get("purpose")
            if not email or not purpose:
                return Response(
                {"error": "Both email and purpose are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

            otp = generate_otp()
            store_otp(email, otp, purpose=purpose)
            send_otp_email(email, otp, purpose)
            return Response(
                    {"message": f"OTP sent to {email} for {purpose}."},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """Verify OTP for signup or password reset"""
    def post(self, request):
        serializer = OtpVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        if not verify_otp(email, otp, purpose):
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if purpose == "signup":
            try:
                user = Users.objects.get(email=email)
                user.is_active = True
                user.save()
            except Users.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Signup successful. Account activated."}, status=status.HTTP_200_OK)

        elif purpose == "password_reset":
            return Response({"message": "OTP verified. You can now reset your password.", "email": email}, status=status.HTTP_200_OK)

# -----------------------------
#  Password Reset
# -----------------------------
class ResetPasswordView(APIView):
    """Reset password after OTP verification"""
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            new_password = serializer.validated_data["new_password"]

            if not is_password_reset_verified(email):
                return Response({"error": "OTP not verified yet"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = Users.objects.get(email=email)
                user.set_password(new_password)
                user.save()
            except Users.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Clear OTP verified flag
            from django.core.cache import cache
            cache.delete(f"{email}_password_reset_verified")

            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
#  User Login
# -----------------------------
class LoginView(APIView):
    """Authenticate user and return JWT tokens"""
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"error": "User not verified"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response(
            {"message": "Login successful", "id": user.id, "refresh": str(refresh), "access": str(refresh.access_token)},
            status=status.HTTP_200_OK,
        )

# -----------------------------
#  User Profile
# -----------------------------
class MyProfileView(APIView):
    """
    Retrieve or update logged-in user's profile
    """
    permission_classes = [IsAuthenticated,IsNormalUser]

    def _get_profile(self, user):
        profile, created = UserProfile.objects.get_or_create(
            user=user
        )
        return profile
    def get(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(profile, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# -----------------------------
#  Change Password (Logged-in User)
# -----------------------------
class ChangePasswordView(APIView):
    """
    Change password for authenticated user
    - Requires JWT token
    - Validates current password
    - Matches new password with confirm password
    """
    permission_classes = [IsAuthenticated,IsNormalUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
#  Deactivate Account
# -----------------------------
class DeactivateAccountView(APIView):
    """
     - JWT token লাগবে (logged-in user)
    - Password confirm করতে হবে
    - Ac   User এর account deactivate করবে
    - Account deactivate হবে (is_active = False)
    """
    permission_classes = [IsAuthenticated,IsNormalUser]

    def post(self, request):
        serializer = DeactivateAccountSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            user.is_active = False  # ✅ Account deactivate করলাম
            user.save()
            
            return Response(
                {"message": "Account deactivated successfully."},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]


class DashboardView(APIView):
    permission_classes = [IsAuthenticated,IsNormalUser]

    def get(self, request, date):
        selected_date = parse_date(date)

        response = {
            "Morning": [],
            "Afternoon": [],
            "Evening": [],
            "Night": [],
            "next_appointment": []
        }

        # ✅ only current user's medicines + load time slots
        medicines = (
            Medicine.objects
            .filter(prescription__users=request.user)
            .select_related(
                "prescription",
                "prescription__doctor",
                "morning",
                "afternoon",
                "evening",
                "night",
            )
        )

        def slot_payload(med, slot_obj):
            return {
                "medicine_name": med.name,
                "time": str(slot_obj.time) if slot_obj and slot_obj.time else None,
                "before_meal": bool(slot_obj.before_meal) if slot_obj else False,
                "after_meal": bool(slot_obj.after_meal) if slot_obj else False,
            }

        for med in medicines:
            start_date = med.prescription.created_at.date()
            end_date = start_date + timedelta(days=med.how_many_day - 1)

            if not (start_date <= selected_date <= end_date):
                continue

            # ✅ new logic: whichever slot exists, put it there
            if med.morning:
                response["Morning"].append(slot_payload(med, med.morning))

            if med.afternoon:
                response["Afternoon"].append(slot_payload(med, med.afternoon))

            if med.evening:
                response["Evening"].append(slot_payload(med, med.evening))

            if med.night:
                response["Night"].append(slot_payload(med, med.night))

        prescriptions = (
            Prescription.objects
            .filter(users=request.user, next_appointment_date=selected_date)
            .select_related("doctor")
        )

        for p in prescriptions:
            response["next_appointment"].append({
                "doctor_name": p.doctor.name if p.doctor else None,
                "appointment_date": p.next_appointment_date
            })

        return Response(response)
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK
        )


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.delete()

        return Response(
            {"message": "Account deleted permanently."},
            status=status.HTTP_200_OK
        )


# ----------------------------- Admin Views -----------------------------


    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

# ----------------------------- Admin Dashboard View -----------------------------

class AdminUpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def put(self, request):
        serializer = AdminChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK
        )

class AdminProfileView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        serializer = AdminProfileSerializer(
            request.user,
            context={"request": request}
        )
        return Response(serializer.data, status=200)

    def put(self, request):
        serializer = AdminProfileSerializer(
            request.user,
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)
    
class AdminDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        total_users = Users.objects.count()

        monthly_users_qs = (
            Users.objects
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_user_data = {d['month'].strftime("%b"): d['count'] for d in monthly_users_qs}


        # Serializer দিয়ে validate এবং structure enforce করা
        serializer = AdminDashboardSerializer(data={
    "total_users": total_users,
    "monthly_user_growth": monthly_user_data,
})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class UserManagementView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    total_users = Users.objects.count()
    def get(self, request):
        users = Users.objects.all()
        total_usaers= Users.objects.count()
        serializer = AdminUserListSerializer(users, many=True)
        return Response({
            "users": serializer.data,
            "total_users": total_usaers
        }, status=200)    
    
    
class DoctorListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        doctors = Doctor.objects.all()
        doctors_count = Doctor.objects.count()
        serializer = DoctorListSerializer(doctors, many=True)
        return Response({
            "doctors": serializer.data,
            "total_doctors": doctors_count
        }, status=200)  
    

class PharmacyListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    
    def get(self,request):
        pharmacies=pharmacy.objects.all()
        pharmacies_count=pharmacy.objects.count()
        serializer=PramcySerializer(pharmacies,many=True)
        return Response({
            "pharmacies":serializer.data,
            "total_pharmacies":pharmacies_count
        },status=200
        )
  

class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        if not token:
            return Response({"detail": "fcm_token required"}, status=400)

        user = request.user
        user.fcm_token = token
        user.save(update_fields=['fcm_token'])

        return Response({"success": True}, status=200)