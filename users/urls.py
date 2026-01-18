from django.urls import path
from .views import RequestOTPView, SignUpView, VerifyOTPView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('request-otp/', RequestOTPView.as_view(), name='request_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
]