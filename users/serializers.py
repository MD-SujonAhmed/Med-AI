from rest_framework import serializers

from doctors.models import Doctor
from .models import Users, UserProfile
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

class SingUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = Users
        fields = ['email', 'full_name', 'password']
        
    def create(self, validated_data):
        user = Users.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if not Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def validate(self, data):
        """
        Check that new_password and confirm_password match.
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match.")
        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance
        
class OtpVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=['signup', 'password_reset'])
    
class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'profile_picture',
            'full_name',
            'email',
            'address',
            'age',
            'health_condition',
            'wakeup_time',
            'breakfast_time',
            'lunch_time',
            'dinner_time',
        ] # email should not be editable

# ✅ Add this new serializer for Change Password
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        """
        Check that current password is correct
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        """
        Check that:
        1. new_password and confirm_password match
        2. new_password is different from current_password
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New password and confirm password do not match."})
        
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from current password."})
        
        return data

    def save(self):
        """
        Update user's password
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    
class DeactivateAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    
    def validate_password(self, value):
        """
        User এর password check করবে deactivate করার আগে
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value
    
#  ------- Dashboard Serializer -------
class MedicineSlotSerializer(serializers.Serializer):
    medicine_name = serializers.CharField()
    before_meal = serializers.BooleanField()
    after_meal = serializers.BooleanField()

class AppointmentSerializer(serializers.Serializer):
    doctor_name = serializers.CharField(allow_null=True)
    appointment_date = serializers.DateField()

class DashboardSerializer(serializers.Serializer):
    Morning = MedicineSlotSerializer(many=True)
    Afternoon = MedicineSlotSerializer(many=True)
    Evening = MedicineSlotSerializer(many=True)
    Night = MedicineSlotSerializer(many=True)
    next_appointment = AppointmentSerializer(many=True)
    
# ------- Logout Serializer -------
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self):
        try:
            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        
# users/serializers.py

class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value

# ----------- Admin Dashboard Serializer -----------
      

class AdminProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(
        source="profile.profile_picture",
        required=False
    )

    class Meta:
        model = Users
        fields = ["id", "full_name", "email", "profile_picture"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})

        instance.full_name = validated_data.get("full_name", instance.full_name)
        instance.email = validated_data.get("email", instance.email)
        instance.save()

        profile, _ = UserProfile.objects.get_or_create(user=instance)

        if "profile_picture" in profile_data:
            profile.profile_picture = profile_data["profile_picture"]
            profile.save()

        return instance
    
        user.save()


class AdminChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user

        if not user.is_superuser:
            raise serializers.ValidationError("Only admin can change admin password")

        if not user.check_password(self.validated_data["old_password"]):
            raise serializers.ValidationError("Old password is incorrect")

        user.set_password(self.validated_data["new_password"])


class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    monthly_user_growth = serializers.DictField(child=serializers.IntegerField())
    

class AdminUserListSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source="profile.address", read_only=True)
    age = serializers.IntegerField(source="profile.age", read_only=True)
    # Count=Users.objects.count()

    class Meta:
        model = Users
        fields = [
            "full_name",
            "email",
            "address",
            "age",
        ]
        

class DoctorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['name', 'sex', 'specialization', 'hospital_name', 'doctor_email']
        



# Project Name: Med Ai
# Description: 
# Auth: 
# Apps:
# Main APIs:
# Swagger URL: https://test15.fireai.agency/api/doc/
# Database: 

