from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import (
    RegisterView,
    UserListView,
    UserDetailView,
    AssignPermissionView,
    ListPermissionsView,
    MyTokenObtainPairView,
    UserUpdateAPIView,
    UserDeleteAPIView,
    UserStatusUpdateAPIView,
    SendOTPView, 
    VerifyOTPView,
    SetNewPasswordView,
    LogoutView,
    UserListViewLatestFive,
    AdminDistributionView,
    UpdatePasswordView,
    CurrentUserDetailView,
    CertificateListCreateView,
    CertificateDetailView,
    UserCertificatesView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users_latest/', UserListViewLatestFive.as_view(), name='user-latest'),
    path('adminDistributionView/', AdminDistributionView.as_view(), name='admin-distribution'),
    path('users/<int:id>/edit/', UserUpdateAPIView.as_view(), name='user-edit'),
    path('users/<int:id>/delete/', UserDeleteAPIView.as_view(), name='user-delete'),
    path('users/<int:id>/status/', UserStatusUpdateAPIView.as_view(), name='user-status-update'),
    path('assign-permissions/', AssignPermissionView.as_view(), name='assign-permissions'),
    path('permissions/', ListPermissionsView.as_view(), name='list-permissions'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set_new_password'),
    path('update-password/', UpdatePasswordView.as_view(), name='update_password'),
    path('current_user/', CurrentUserDetailView.as_view(), name='current_user'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Certificate endpoints
    path('certificates/', CertificateListCreateView.as_view(), name='certificate-list-create'),
    path('certificates/<int:id>/', CertificateDetailView.as_view(), name='certificate-detail'),
    path('users/<int:user_id>/certificates/', UserCertificatesView.as_view(), name='user-certificates'),
]
