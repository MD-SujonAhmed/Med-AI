from django.urls import path
from .views import (
    SignUpView,
    RequestOTPView,
    VerifyOTPView,
    ResendOTPView,
    ResetPasswordView,
    LoginView,
    MyProfileView,
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
] 
