import random
from datetime import datetime, timedelta
from django.utils import timezone

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
from django.db.models import Count, Q, Avg, Sum
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


class BusinessInsightsKPIView(APIView):
    """
    API endpoint to get Business Insights KPIs for admin dashboard
    Returns client progress, goal attainment, staff productivity, caseload, and appointment statistics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Import session models
            from session.models import Session, GoalProgress
            from treatment_plan.models import TreatmentPlan, TreatmentGoal
            
            # Get date filters from query params (optional)
            days_back = int(request.query_params.get('days', 7))  # Default to last 7 days
            start_date = timezone.now().date() - timedelta(days=days_back)
            end_date = timezone.now().date()
            
            # 1. CLIENT PROGRESS & GOAL ATTAINMENT
            # Get all clients
            clients = CustomUser.objects.filter(role__name='Clients/Parent').order_by('id')[:5]
            
            client_progress_data = []
            for client in clients:
                # Get all sessions for this client
                client_sessions = Session.objects.filter(client=client)
                
                # Get all goals for this client from treatment plans
                # Note: TreatmentPlan.client_id is a CharField, so we need to convert to string
                treatment_plans = TreatmentPlan.objects.filter(client_id=str(client.id))
                total_goals = TreatmentGoal.objects.filter(treatment_plan__in=treatment_plans).count()
                
                # Get goal progress from sessions
                goal_progresses = GoalProgress.objects.filter(session__client=client)
                total_goal_progress = goal_progresses.count()
                met_goals = goal_progresses.filter(is_met=True).count()
                
                # Calculate progress percentage (based on goal progress entries)
                progress_percentage = (met_goals / total_goal_progress * 100) if total_goal_progress > 0 else 0
                
                # Calculate goal attainment (achieved goals vs total goals)
                achieved_goals = TreatmentGoal.objects.filter(
                    treatment_plan__in=treatment_plans,
                    is_achieved=True
                ).count()
                goal_attainment = (achieved_goals / total_goals * 100) if total_goals > 0 else 0
                
                client_progress_data.append({
                    'client_name': client.name or client.username or f'Client {client.id}',
                    'client_id': client.id,
                    'progress': round(progress_percentage, 2),
                    'goal_attainment': round(goal_attainment, 2)
                })
            
            # 2. STAFF PRODUCTIVITY & CASELOAD (Weekly data)
            staff_members = CustomUser.objects.filter(role__name__in=['RBT', 'BCBA'])
            
            # Get last 7 days for weekly chart
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_data = []
            
            for day_offset in range(7):
                day_date = end_date - timedelta(days=6-day_offset)
                day_name = day_date.strftime('%A')
                
                # Calculate caseload (number of unique clients assigned to staff)
                total_caseload = 0
                for staff in staff_members:
                    # Count clients assigned to this staff member
                    caseload_count = Session.objects.filter(
                        staff=staff,
                        session_date=day_date
                    ).values('client').distinct().count()
                    total_caseload += caseload_count
                
                # Calculate staff productivity (completed sessions per staff)
                total_productivity = Session.objects.filter(
                    staff__role__name__in=['RBT', 'BCBA'],
                    session_date=day_date,
                    status='completed'
                ).count()
                
                # Average productivity per staff member
                avg_productivity = (total_productivity / staff_members.count()) if staff_members.count() > 0 else 0
                
                weekly_data.append({
                    'day': day_name,
                    'date': day_date.isoformat(),
                    'caseload': total_caseload,
                    'productivity': round(avg_productivity, 2)
                })
            
            # 3. APPOINTMENT & CANCELLATION RATES
            # Get all sessions in the date range
            all_sessions = Session.objects.filter(
                session_date__gte=start_date,
                session_date__lte=end_date
            )
            
            completed_sessions = all_sessions.filter(status='completed').count()
            cancelled_sessions = all_sessions.filter(status='cancelled').count()
            total_appointments = completed_sessions + cancelled_sessions
            
            attendance_rate = (completed_sessions / total_appointments * 100) if total_appointments > 0 else 0
            cancellation_rate = (cancelled_sessions / total_appointments * 100) if total_appointments > 0 else 0
            
            appointment_data = {
                'attendance_rate': round(attendance_rate, 2),
                'cancellation_rate': round(cancellation_rate, 2),
                'total_appointments': total_appointments,
                'completed': completed_sessions,
                'cancelled': cancelled_sessions
            }
            
            # 4. ADDITIONAL INSIGHTS
            # Get insights based on the data
            insights = []
            
            # Client Progress Insight
            if client_progress_data:
                avg_goal_attainment = sum([c['goal_attainment'] for c in client_progress_data]) / len(client_progress_data)
                if avg_goal_attainment >= 70:
                    insights.append({
                        'title': 'Client Progress And Goal Attainment Rates',
                        'insight': f'High success rate ({avg_goal_attainment:.1f}%) indicates a strong, marketable service. Consider expanding the service, creating group programs, or using it as a case study in marketing materials to attract new clients.'
                    })
            
            # Staff Productivity Insight
            if weekly_data:
                avg_caseload = sum([d['caseload'] for d in weekly_data]) / len(weekly_data)
                avg_productivity = sum([d['productivity'] for d in weekly_data]) / len(weekly_data)
                
                if avg_caseload > 10:  # High caseload threshold
                    insights.append({
                        'title': 'Staff Productivity And Caseload Efficiency',
                        'insight': 'Some staff members are over-booked. It may be time to hire or invest in training for less utilized staff. Highly efficient staff could mentor new hires to balance workload, prevent burnout, and ensure the practice can handle more clients.'
                    })
                elif avg_productivity < 5:
                    insights.append({
                        'title': 'Staff Productivity And Caseload Efficiency',
                        'insight': 'Staff productivity is below optimal levels. Consider additional training or support to improve efficiency.'
                    })
            
            # Cancellation Rate Insight
            if cancellation_rate > 20:
                insights.append({
                    'title': 'Appointment Attendance And Cancellation Rates',
                    'insight': f'A high cancellation rate ({cancellation_rate:.1f}%) could indicate a need for more proactive reminders or a re-evaluation of booking policies. Reducing cancellations is linked to more consistent revenue and a better client experience.'
                })
            
            return Response({
                'client_progress': client_progress_data,
                'staff_productivity': weekly_data,
                'appointment_stats': appointment_data,
                'insights': insights,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days_back
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Failed to retrieve business insights KPIs'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)