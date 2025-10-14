import random

from django.contrib.auth import get_user_model
from rest_framework import generics, status, response, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser, Role, Permission, OTP, Certificate
from .serializers import UserSerializer, RegisterSerializer, AssignPermissionSerializer, MyTokenObtainPairSerializer, RoleSerializer, UserStatusSerializer, SendOTPSerializer, VerifyOTPSerializer, SetNewPasswordSerializer, CertificateSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.hashers import make_password, check_password

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import logout
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()

# Register view
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAuthenticated]  # Require authentication

# Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10              # default items per page
    page_size_query_param = 'page_size'  # allow client to override
    max_page_size = 10 

# List all users
class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.filter(role__name="Admin").order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        total_count = CustomUser.objects.filter(role__name="Admin").count()
        active_count = CustomUser.objects.filter(role__name="Admin", status="Active").count()
        data = {
            'total_count': total_count,
            'active_count': active_count,
            'latest_users': serializer.data
        }
        if page is not None:
            return self.get_paginated_response(data)
        return response.Response(data)

class AdminDistributionView(APIView):
    permission_classes = []  # Add your permissions if needed

    def get(self, request):
        # Filter only Admins
        admin_users = CustomUser.objects.filter(role__name="Admin")
        
        # Aggregate count by status
        distribution = admin_users.values('status').annotate(count=Count('id'))

        # Convert to a dict like {"Active": 10, "Inactive": 5, "Pending": 3}
        distribution_dict = {item['status']: item['count'] for item in distribution}

        return Response({
            'distribution': distribution_dict,
            'total_admins': admin_users.count()
        })

# User detail
class UserListViewLatestFive(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get latest 5 Admin users
        return CustomUser.objects.filter(role__name="Admin").order_by('-id')[:5]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Calculate total count and active count
        total_count = CustomUser.objects.filter(role__name="Admin").count()
        active_count = CustomUser.objects.filter(role__name="Admin", status="Active").count()

        return response.Response({
            'total_count': total_count,
            'active_count': active_count,
            'latest_users': serializer.data
        })
# User detail
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

# User edit
class UserUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        """ if 'extra_permissions' in request.data:
            if request.user.role.name != 'Admin':
                return Response(
                    {'detail': 'Not allowed to edit permissions'}, 
                    status=403
                ) """

        return super().update(request, *args, **kwargs)

# User delete
class UserDeleteAPIView(generics.DestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer  # optional, DRF doesn't actually use it for delete
    permission_classes = [IsAuthenticated]
    lookup_field = 'id' 
  
# Assign permissions dynamically
class AssignPermissionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role.name != 'Superadmin':
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AssignPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        permissions = serializer.validated_data['permissions']

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        permission_objs = Permission.objects.filter(codename__in=permissions)
        user.extra_permissions.set(permission_objs)
        user.save()

        return Response({'detail': 'Permissions assigned successfully'})

class ListPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_role = request.user.role

        if not user_role:
            return Response({'detail': 'User has no role assigned'}, status=403)

        # Example logic: Superadmin sees all role permissions
        if user_role.name == 'superadmin':
            roles = Role.objects.all()
        else:
            # Other roles see only their own role permissions
            roles = Role.objects.filter(id=user_role.id)

        result = {}
        for role in roles:
            perms = role.permissions.all()
            result[role.name] = [{"code": p.codename, "label": p.name} for p in perms]

        return Response(result)
# JWT Token view
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]  # No authentication required for login

class UserStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserStatusSerializer
    permission_classes = [IsAuthenticated]  # only admins can update status
    lookup_field = 'id'  # URL: users/<int:id>/status/

class SendOTPView(generics.GenericAPIView):
    serializer_class = SendOTPSerializer
    permission_classes = [permissions.AllowAny]  # No authentication required for password reset

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP
        otp_code = str(random.randint(1000, 9999))
        OTP.objects.create(user=user, code=otp_code)

        # Send email (use console backend for testing)
        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP code is {otp_code}",
            from_email="no-reply@example.com",
            recipient_list=[email],
        )

        return Response({"message": "OTP sent successfully"})
    
class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [permissions.AllowAny]  # No authentication required for password reset

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
            otp = OTP.objects.filter(user=user, code=code).order_by('-created_at').first()
        except (User.DoesNotExist, OTP.DoesNotExist):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp and otp.is_valid():
            otp.delete()  # optional: delete OTP after successful verification
            return Response({"message": "OTP verified successfully"})
        else:
            return Response({"error": "OTP expired or invalid"}, status=status.HTTP_400_BAD_REQUEST)

class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]  # No authentication required for password reset

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")  # Pass user_id from OTP verification step
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
    

class UpdatePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check old password against stored hash
        if not check_password(old_password, user.password):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "New password and confirm password do not match"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except Exception as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        # Hash the new password before saving
        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
    
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
        }
        return Response(data)


# Certificate Views
class CertificateListCreateView(generics.ListCreateAPIView):
    """
    List all certificates or create a new certificate
    """
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # If user_id is provided in query params, filter by that user
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            return Certificate.objects.filter(user_id=user_id)
        # Otherwise return all certificates
        return Certificate.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class CertificateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a certificate
    """
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


class UserCertificatesView(generics.ListAPIView):
    """
    List all certificates for a specific user
    """
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Certificate.objects.filter(user_id=user_id)