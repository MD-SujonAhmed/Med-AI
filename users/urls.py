from django.urls import path
from .views import (
    AdminDashboardStatsView,
    DashboardView,
    DoctorListView,
    SaveFCMTokenView,
    SignUpView,
    RequestOTPView,
    UserManagementView,
    VerifyOTPView,
    ResetPasswordView,
    LoginView,
    MyProfileView,
    ChangePasswordView,
    DeactivateAccountView,
    AdminProfileView,
    AdminUpdatePasswordView,
    LogoutView,
    DeleteAccountView,
    PharmacyListView,
)

urlpatterns = [
    # User Registration & OTP
    path('signup/', SignUpView.as_view(), name='user_signup'),
    path('otp/request/', RequestOTPView.as_view(), name='request_otp'),
    path('otp/verify/', VerifyOTPView.as_view(), name='verify_otp'),

    # Authentication
    path('login/', LoginView.as_view(), name='user_login'),
    path('password/reset/', ResetPasswordView.as_view(), name='reset_password'),
    
    # Logout
    path('logout/', LogoutView.as_view(), name='user_logout'),  
    
    # Delete Account
    path('account/delete/', DeleteAccountView.as_view(), name='delete_account'),
    # User Profile ,# JWT required 
    path('profile/', MyProfileView.as_view(), name='user_profile'),
    
    # Change Password (JWT required)
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),
    # Deactivate Account (JWT required)
    path('account/deactivate/', DeactivateAccountView.as_view(), name='deactivate_account'),
    
    # Admin Profile & Change Password (JWT + Admin Role required)
    path('admin/profile/', AdminProfileView.as_view(), name='admin_profile'),   
    path('admin/password/change/', AdminUpdatePasswordView.as_view(), name='admin_change_password'),
    
    # User Dashboard
    path('dashboard/<date>/', DashboardView.as_view(), name='user_dashboard'),
    # Admin Dashboard
    path('admin/dashboard/', AdminDashboardStatsView.as_view(), name='admin_dashboard'),
    path('admin/users/', UserManagementView.as_view(), name='admin_user_management'),
    path('admin/doctors/', DoctorListView.as_view(), name='admin_doctor_list'),
    path('admin/pharmacists/', PharmacyListView.as_view(), name='admin_pharmacist_list'),
    
    path('fcm/token/', SaveFCMTokenView.as_view(), name='save_fcm_token'),
    

]