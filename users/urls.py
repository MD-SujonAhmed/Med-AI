from django.urls import path
from .views import (
    DashboardView,
    SignUpView,
    RequestOTPView,
    VerifyOTPView,
    ResendOTPView,
    ResetPasswordView,
    LoginView,
    MyProfileView,
    ChangePasswordView,
    DeactivateAccountView,
    AdminProfileView,
    AdminUpdatePasswordView,
)

urlpatterns = [
    # User Registration & OTP
    path('signup/', SignUpView.as_view(), name='user_signup'),
    path('otp/request/', RequestOTPView.as_view(), name='request_otp'),
    path('otp/verify/', VerifyOTPView.as_view(), name='verify_otp'),
    path('otp/resend/', ResendOTPView.as_view(), name='resend_otp'),

    # Authentication
    path('login/', LoginView.as_view(), name='user_login'),
    path('password/reset/', ResetPasswordView.as_view(), name='reset_password'),

    # User Profile ,# JWT required 
    path('profile/', MyProfileView.as_view(), name='user_profile'),
    
        # Change Password (JWT required) ✅ Add this line
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),
    # Deactivate Account (JWT required) ✅ Add this line
    path('account/deactivate/', DeactivateAccountView.as_view(), name='deactivate_account'),
    
    # Admin Profile & Change Password (JWT + Admin Role required) ✅ Add these lines
    path('admin/profile/', AdminProfileView.as_view(), name='admin_profile'),   
    path('admin/password/change/', AdminUpdatePasswordView.as_view(), name='admin_change_password'),
    
    # Dashboard
    path('dashboard/<date>/', DashboardView.as_view(), name='user_dashboard'),
] 

