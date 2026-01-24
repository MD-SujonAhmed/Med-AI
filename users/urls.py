from django.urls import path
from .views import LoginView, RequestOTPView, ResendOTPView, SignUpView, VerifyOTPView, ResetPasswordView, MyProfileView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('forgot-password-otp/', RequestOTPView.as_view(), name='forgot_password_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('login/', LoginView.as_view(), name='login'),
    # JWT required
    path("profile/", MyProfileView.as_view(), name="my_profile"),
    
    
    
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'YOUR_GOOGLE_CLIENT_ID'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'