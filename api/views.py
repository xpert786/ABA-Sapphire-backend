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
    Matches the Business Insights dashboard screenshot format
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Check if user is Admin or Superadmin
            user = request.user
            if hasattr(user, 'role') and user.role:
                role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
                if role_name not in ['Admin', 'Superadmin']:
                    return Response({
                        'error': 'Only Admin and Superadmin users can access business insights'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Import session models
            from session.models import Session, GoalProgress
            from treatment_plan.models import TreatmentPlan, TreatmentGoal
            
            # Get date filters from query params (optional)
            period_filter = request.query_params.get('period', 'last_week')  # last_week, last_month, etc.
            
            if period_filter == 'last_week':
                days_back = 7
            elif period_filter == 'last_month':
                days_back = 30
            elif period_filter == 'last_quarter':
                days_back = 90
            else:
                days_back = int(request.query_params.get('days', 7))  # Default to last 7 days
            
            start_date = timezone.now().date() - timedelta(days=days_back)
            end_date = timezone.now().date()
            
            # 1. CLIENT PROGRESS & GOAL ATTAINMENT (Bar Chart Data)
            # Get top 5 clients by activity
            clients = CustomUser.objects.filter(role__name='Clients/Parent').order_by('-date_joined')[:5]
            
            client_progress_data = []
            for idx, client in enumerate(clients, 1):
                # Get sessions for this client in the period
                client_sessions = Session.objects.filter(
                    client=client,
                    session_date__gte=start_date,
                    session_date__lte=end_date
                )
                
                # Get all goals for this client from treatment plans
                treatment_plans = TreatmentPlan.objects.filter(
                    Q(client_id=str(client.id)) |
                    Q(client_id=client.username) |
                    Q(client_id=getattr(client, 'staff_id', '')) |
                    Q(client_name__icontains=client.name if hasattr(client, 'name') and client.name else '')
                )
                total_goals = TreatmentGoal.objects.filter(treatment_plan__in=treatment_plans).count()
                
                # Get goal progress from sessions in period
                completed_session_ids = client_sessions.filter(status='completed').values_list('id', flat=True)
                goal_progresses = GoalProgress.objects.filter(session_id__in=completed_session_ids)
                total_goal_progress = goal_progresses.count()
                met_goals = goal_progresses.filter(is_met=True).count()
                
                # Calculate client progress percentage (based on goal progress entries)
                progress_percentage = (met_goals / total_goal_progress * 100) if total_goal_progress > 0 else 0
                
                # Calculate goal attainment (achieved goals vs total goals)
                achieved_goals = TreatmentGoal.objects.filter(
                    treatment_plan__in=treatment_plans,
                    is_achieved=True
                ).count()
                goal_attainment = (achieved_goals / total_goals * 100) if total_goals > 0 else 0
                
                # Use client name or generate Client A, B, C, etc.
                client_name = client.name or client.username or f'Client {chr(64 + idx)}'  # A, B, C, D, E
                if not client.name and not client.username:
                    client_name = f'Client {chr(64 + idx)}'
                
                client_progress_data.append({
                    'client_name': client_name,
                    'client_id': client.id,
                    'client_progress': round(progress_percentage, 0),
                    'goal_attainment': round(goal_attainment, 0)
                })
            
            # 2. STAFF PRODUCTIVITY & CASELOAD (Line Chart - Weekly Data)
            staff_members = CustomUser.objects.filter(role__name__in=['RBT', 'BCBA'])
            
            # Get last 7 days for weekly chart (Mon-Sun)
            today = timezone.now().date()
            # Find the Monday of the current week
            days_since_monday = today.weekday()  # 0 = Monday, 6 = Sunday
            monday_date = today - timedelta(days=days_since_monday)
            
            days_of_week_abbr = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
            weekly_data = []
            
            for day_offset in range(7):
                day_date = monday_date + timedelta(days=day_offset)
                day_name = days_of_week_abbr[day_offset]
                
                # Calculate caseload (total unique clients with sessions on this day)
                caseload_count = Session.objects.filter(
                    staff__role__name__in=['RBT', 'BCBA'],
                    session_date=day_date
                ).values('client').distinct().count()
                
                # Calculate staff productivity (average completed sessions per staff member)
                total_completed_sessions = Session.objects.filter(
                    staff__role__name__in=['RBT', 'BCBA'],
                    session_date=day_date,
                    status='completed'
                ).count()
                
                # Average productivity per staff member
                staff_count = staff_members.count()
                avg_productivity = (total_completed_sessions / staff_count * 10) if staff_count > 0 else 0  # Scale for visibility
                
                weekly_data.append({
                    'day': day_name,
                    'day_full': day_date.strftime('%A'),
                    'date': day_date.isoformat(),
                    'caseload': caseload_count,
                    'productivity': round(avg_productivity, 1)
                })
            
            # 3. APPOINTMENT & CANCELLATION RATES (Pie Chart Data)
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
                'attendance_rate': round(attendance_rate, 0),
                'cancellation_rate': round(cancellation_rate, 0),
                'total_appointments': total_appointments,
                'completed': completed_sessions,
                'cancelled': cancelled_sessions
            }
            
            # 4. GROWTH OPPORTUNITIES FROM PERFORMANCE TRENDS (Insights)
            growth_opportunities = []
            
            # Client Progress & Goal Attainment Insight
            if client_progress_data:
                avg_goal_attainment = sum([c['goal_attainment'] for c in client_progress_data]) / len(client_progress_data)
                if avg_goal_attainment >= 60:
                    growth_opportunities.append({
                        'id': 'client_progress_insight',
                        'category': 'Client Progress And Goal Attainment Rates',
                        'title': 'Client Progress And Goal Attainment Rates',
                        'insight': 'A High Success Rate Indicates A Strong, Marketable Service. You Could Consider Expanding This Service, Creating A Group Program Around It, Or Using It As A Case Study In Your Marketing Materials To Attract New Clients.',
                        'icon': 'pencil',
                        'actionable': True
                    })
            
            # Staff Productivity & Caseload Insight
            if weekly_data:
                avg_caseload = sum([d['caseload'] for d in weekly_data]) / len(weekly_data)
                avg_productivity = sum([d['productivity'] for d in weekly_data]) / len(weekly_data)
                
                # Check if any staff are over-booked
                max_caseload = max([d['caseload'] for d in weekly_data]) if weekly_data else 0
                if max_caseload > 8 or avg_caseload > 6:
                    growth_opportunities.append({
                        'id': 'staff_productivity_insight',
                        'category': 'Staff Productivity And Caseload Efficiency',
                        'title': 'Staff Productivity And Caseload Efficiency',
                        'insight': 'If Some Staff Members Are Over-Booked, It May Be Time To Hire Or Invest In Training For Less Utilized Staff. Conversely, A Staff Member With High Efficiency Could Be A Perfect Mentor For New Hires. This Helps You Balance The Workload, Prevent Burnout, And Ensure Your Practice Can Handle More Clients.',
                        'icon': 'pencil',
                        'actionable': True
                    })
                elif avg_productivity < 5:
                    growth_opportunities.append({
                        'id': 'staff_productivity_insight',
                        'category': 'Staff Productivity And Caseload Efficiency',
                        'title': 'Staff Productivity And Caseload Efficiency',
                        'insight': 'Staff productivity is below optimal levels. Consider additional training or support to improve efficiency.',
                        'icon': 'pencil',
                        'actionable': True
                    })
            
            # Appointment & Cancellation Insight
            if cancellation_rate >= 15:
                # Check for day-specific cancellation patterns
                day_cancellations = {}
                for day_data in weekly_data:
                    day_sessions = Session.objects.filter(
                        session_date=day_data['date'],
                        status='cancelled'
                    ).count()
                    day_cancellations[day_data['day']] = day_sessions
                
                max_cancel_day = max(day_cancellations.items(), key=lambda x: x[1]) if day_cancellations else None
                
                insight_text = f'A High Cancellation Rate ({cancellation_rate:.0f}%) Could Indicate A Need For More Proactive Reminders Or A Re-Evaluation Of Your Booking Policies. Reducing Cancellations Means More Consistent Revenue And A Better Client Experience.'
                if max_cancel_day and max_cancel_day[1] > 0:
                    insight_text = f'A High Cancellation Rate On {max_cancel_day[0]}s, For Example, Could Indicate A Need For More Proactive Reminders Or A Re-Evaluation Of Your Booking Policies. Reducing Cancellations Means More Consistent Revenue And A Better Client Experience.'
                
                growth_opportunities.append({
                    'id': 'appointment_cancellation_insight',
                    'category': 'Appointment Attendance And Cancellation Rates',
                    'title': 'Appointment Attendance And Cancellation Rates',
                    'insight': insight_text,
                    'icon': 'pencil',
                    'actionable': True
                })
            
            # Prepare response matching screenshot format
            return Response({
                'title': 'Business Insights',
                'subtitle': 'Make Informed Decisions Faster With Accurate And Reliable Business Intelligence',
                'client_progress_and_goal_attainment': {
                    'type': 'bar_chart',
                    'data': client_progress_data,
                    'x_axis_label': 'Clients',
                    'y_axis_max': 80,
                    'series': [
                        {'name': 'Client Progress', 'color': 'green'},
                        {'name': 'Goal Attainment', 'color': 'gold'}
                    ],
                    'filter': period_filter,
                    'filter_display': period_filter.replace('_', ' ').title()
                },
                'staff_productivity_and_caseload': {
                    'type': 'line_chart',
                    'data': weekly_data,
                    'x_axis_label': 'Days of Week',
                    'y_axis_max': 100,
                    'series': [
                        {'name': 'Caseload', 'type': 'solid', 'color': 'blue'},
                        {'name': 'Staff Productivity', 'type': 'dashed', 'color': 'blue'}
                    ]
                },
                'appointment_and_cancellation': {
                    'type': 'pie_chart',
                    'data': appointment_data,
                    'segments': [
                        {
                            'label': 'Attendance Rate',
                            'value': attendance_rate,
                            'display': f'{round(attendance_rate, 0)}%',
                            'color': 'green'
                        },
                        {
                            'label': 'Cancellation Rate',
                            'value': cancellation_rate,
                            'display': f'{round(cancellation_rate, 0)}%',
                            'color': 'gold'
                        }
                    ]
                },
                'growth_opportunities': growth_opportunities,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days_back,
                    'period_filter': period_filter
                },
                'calculated_at': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'message': 'Failed to retrieve business insights KPIs'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminDashboardView(APIView):
    """
    Comprehensive Admin Dashboard API endpoint
    Returns all data needed for the admin dashboard including:
    - Quick Actions
    - Client Progress & Goal Attainment
    - Staff Productivity & Caseload
    - Document Management
    - Legal Obligations
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Check if user is Admin or Superadmin
            user = request.user
            if hasattr(user, 'role') and user.role:
                role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
                if role_name not in ['Admin', 'Superadmin']:
                    return Response({
                        'error': 'Only Admin and Superadmin users can access the dashboard'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Import required models
            from session.models import Session, GoalProgress
            from treatment_plan.models import TreatmentPlan, TreatmentGoal
            
            # Get date filter from query params
            days_back = int(request.query_params.get('days', 7))  # Default to last 7 days
            start_date = timezone.now().date() - timedelta(days=days_back)
            end_date = timezone.now().date()
            
            # 1. QUICK ACTIONS
            quick_actions = [
                {
                    'id': 'practice_management',
                    'title': 'Practice Management',
                    'description': 'Manage practice settings and configurations',
                    'icon': 'document',
                    'route': '/practice-management'
                },
                {
                    'id': 'business_insights',
                    'title': 'Business Insights',
                    'description': 'View detailed business analytics and reports',
                    'icon': 'bar-chart',
                    'route': '/business-insights'
                },
                {
                    'id': 'payroll_management',
                    'title': 'Payroll Management',
                    'description': 'Manage staff payroll and payments',
                    'icon': 'clock',
                    'route': '/payroll-management'
                },
                {
                    'id': 'messages',
                    'title': 'Messages',
                    'description': 'View and manage messages',
                    'icon': 'chat',
                    'route': '/messages'
                },
                {
                    'id': 'scheduling',
                    'title': 'Scheduling',
                    'description': 'Manage appointments and schedules',
                    'icon': 'calendar',
                    'route': '/scheduling'
                }
            ]
            
            # 2. CLIENT PROGRESS & GOAL ATTAINMENT
            clients = CustomUser.objects.filter(role__name='Clients/Parent').order_by('id')[:5]
            
            client_progress_data = []
            for client in clients:
                client_sessions = Session.objects.filter(client=client)
                treatment_plans = TreatmentPlan.objects.filter(client_id=str(client.id))
                total_goals = TreatmentGoal.objects.filter(treatment_plan__in=treatment_plans).count()
                goal_progresses = GoalProgress.objects.filter(session__client=client)
                total_goal_progress = goal_progresses.count()
                met_goals = goal_progresses.filter(is_met=True).count()
                progress_percentage = (met_goals / total_goal_progress * 100) if total_goal_progress > 0 else 0
                achieved_goals = TreatmentGoal.objects.filter(
                    treatment_plan__in=treatment_plans,
                    is_achieved=True
                ).count()
                goal_attainment = (achieved_goals / total_goals * 100) if total_goals > 0 else 0
                
                client_progress_data.append({
                    'client_id': client.id,
                    'client_name': client.name or client.username or f'Client {client.id}',
                    'progress': round(progress_percentage, 2),
                    'goal_attainment': round(goal_attainment, 2)
                })
            
            # 3. STAFF PRODUCTIVITY & CASELOAD (Weekly data)
            staff_members = CustomUser.objects.filter(role__name__in=['RBT', 'BCBA'])
            weekly_data = []
            
            for day_offset in range(7):
                day_date = end_date - timedelta(days=6-day_offset)
                day_name = day_date.strftime('%A')
                
                total_caseload = 0
                for staff in staff_members:
                    caseload_count = Session.objects.filter(
                        staff=staff,
                        session_date=day_date
                    ).values('client').distinct().count()
                    total_caseload += caseload_count
                
                total_productivity = Session.objects.filter(
                    staff__role__name__in=['RBT', 'BCBA'],
                    session_date=day_date,
                    status='completed'
                ).count()
                
                avg_productivity = (total_productivity / staff_members.count()) if staff_members.count() > 0 else 0
                
                weekly_data.append({
                    'day': day_name,
                    'date': day_date.isoformat(),
                    'caseload': total_caseload,
                    'productivity': round(avg_productivity, 2)
                })
            
            # 4. DOCUMENT MANAGEMENT
            # Get documents from user intake documents and certificates
            documents = []
            
            # Get intake documents from users (BAA, Compliance Reports, etc.)
            # Check users with uploaded documents
            users_with_docs = CustomUser.objects.filter(
                Q(consent_for_treatment__isnull=False) |
                Q(hippa_authorization__isnull=False) |
                Q(insurance_card__isnull=False) |
                Q(physician_referral__isnull=False) |
                Q(previous_assessment__isnull=False) |
                Q(iep__isnull=False)
            ).distinct()
            
            # Add BAA documents (HIPAA Authorization)
            for user in users_with_docs.filter(hippa_authorization__isnull=False):
                if user.hippa_authorization:
                    # Use date_joined as fallback if updated_at doesn't exist
                    last_updated = None
                    if hasattr(user, 'date_joined') and user.date_joined:
                        last_updated = user.date_joined.strftime('%m/%d/%Y')
                    documents.append({
                        'id': f'baa_{user.id}',
                        'name': 'Business Associate Agreement (BAA)',
                        'type': 'BAA',
                        'last_updated': last_updated,
                        'file_url': user.hippa_authorization.url if user.hippa_authorization else None,
                        'client_name': user.name or user.username
                    })
            
            # Add compliance reports (from user documents - could be from previous_assessment or consent_for_treatment)
            compliance_users = users_with_docs.filter(
                Q(previous_assessment__isnull=False) | Q(consent_for_treatment__isnull=False)
            )
            for user in compliance_users:
                last_updated = None
                if hasattr(user, 'date_joined') and user.date_joined:
                    last_updated = user.date_joined.strftime('%m/%d/%Y')
                
                if user.previous_assessment:
                    documents.append({
                        'id': f'compliance_{user.id}_assessment',
                        'name': 'Annual Compliance Report',
                        'type': 'Compliance Report',
                        'last_updated': last_updated,
                        'file_url': user.previous_assessment.url if user.previous_assessment else None,
                        'client_name': user.name or user.username
                    })
                if user.consent_for_treatment:
                    documents.append({
                        'id': f'compliance_{user.id}_consent',
                        'name': 'Annual Compliance Report',
                        'type': 'Compliance Report',
                        'last_updated': last_updated,
                        'file_url': user.consent_for_treatment.url if user.consent_for_treatment else None,
                        'client_name': user.name or user.username
                    })
            
            # Get certificates (staff certifications)
            from api.models import Certificate
            certificates = Certificate.objects.select_related('user').order_by('-updated_at')[:5]
            for cert in certificates:
                if cert.certificate_file:
                    documents.append({
                        'id': f'cert_{cert.id}',
                        'name': f'{cert.name} - {cert.user.name or cert.user.username}',
                        'type': 'Certificate',
                        'last_updated': cert.updated_at.strftime('%m/%d/%Y') if cert.updated_at else None,
                        'file_url': cert.certificate_file.url if cert.certificate_file else None,
                        'client_name': cert.user.name or cert.user.username
                    })
            
            # Sort documents by last_updated (most recent first)
            documents.sort(key=lambda x: x['last_updated'] or '', reverse=True)
            # Get top 3 documents
            documents = documents[:3]
            
            # 5. LEGAL OBLIGATIONS
            legal_obligations = [
                {
                    'id': 'hipaa_billing',
                    'title': 'HIPAA & Billing Requirements',
                    'description': 'This System Helps Monitor And Ensure Compliance With State & Federal Laws Like HIPAA To Protect Client Data & Ensure Proper Billing Practices.',
                    'type': 'Compliance',
                    'icon': 'document',
                    'status': 'active',
                    'last_reviewed': timezone.now().date().isoformat()
                },
                {
                    'id': 'data_privacy',
                    'title': 'Data Privacy & Security',
                    'description': 'Ensures all client data is protected according to HIPAA regulations and state privacy laws.',
                    'type': 'Privacy',
                    'icon': 'shield',
                    'status': 'active',
                    'last_reviewed': timezone.now().date().isoformat()
                }
            ]
            
            # 6. APPOINTMENT STATISTICS
            all_sessions = Session.objects.filter(
                session_date__gte=start_date,
                session_date__lte=end_date
            )
            completed_sessions = all_sessions.filter(status='completed').count()
            cancelled_sessions = all_sessions.filter(status='cancelled').count()
            total_appointments = completed_sessions + cancelled_sessions
            attendance_rate = (completed_sessions / total_appointments * 100) if total_appointments > 0 else 0
            cancellation_rate = (cancelled_sessions / total_appointments * 100) if total_appointments > 0 else 0
            
            appointment_stats = {
                'attendance_rate': round(attendance_rate, 2),
                'cancellation_rate': round(cancellation_rate, 2),
                'total_appointments': total_appointments,
                'completed': completed_sessions,
                'cancelled': cancelled_sessions
            }
            
            return Response({
                'quick_actions': quick_actions,
                'client_progress': {
                    'data': client_progress_data,
                    'filter': f'Last {days_back} days',
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'days': days_back
                    }
                },
                'staff_productivity': {
                    'data': weekly_data,
                    'legend': {
                        'caseload': 'Caseload',
                        'productivity': 'Staff Productivity'
                    }
                },
                'document_management': {
                    'documents': documents,
                    'total_documents': len(documents)
                },
                'legal_obligations': legal_obligations,
                'appointment_stats': appointment_stats,
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'message': 'Failed to retrieve admin dashboard data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientDashboardView(APIView):
    """
    API endpoint for client dashboard data
    Returns all dashboard information including:
    - Welcome section
    - Next Appointment
    - Last Session Summary
    - Progress Report Status
    - Session Attendance Overview
    - Treatment Plan
    - Overall Progress
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Check if user is a client
            if not hasattr(user, 'role') or not user.role:
                return Response({
                    'error': 'User role not found'
                }, status=status.HTTP_403_FORBIDDEN)
            
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            # Only clients can access their own dashboard
            if role_name != 'Clients/Parent':
                return Response({
                    'error': 'This endpoint is only available for clients'
                }, status=status.HTTP_403_FORBIDDEN)
            
            client = user
            
            # Import models
            from session.models import Session as TherapySession, GoalProgress, Activity, Incident
            from scheduler.models import Session as SchedulerSession
            from treatment_plan.models import TreatmentPlan, TreatmentGoal
            from django.db.models import Q, Count, Case, When, IntegerField
            from datetime import datetime, timedelta
            from django.utils import timezone as tz
            
            today = tz.now().date()
            now = tz.now()
            
            # 1. WELCOME SECTION
            welcome_data = {
                'client_name': client.name or client.get_full_name() or client.username,
                'subtitle': "Here's An Overview Of Your Child's ABA Therapy Journey."
            }
            
            # 2. NEXT APPOINTMENT
            # Check both scheduler sessions and therapy sessions
            next_appointment = None
            try:
                # First try scheduler sessions (scheduled appointments)
                scheduler_session = SchedulerSession.objects.filter(
                    client=client,
                    session_date__gte=today
                ).order_by('session_date', 'start_time').first()
                
                if scheduler_session:
                    # Format date and time
                    session_datetime = datetime.combine(scheduler_session.session_date, scheduler_session.start_time)
                    day_name = session_datetime.strftime('%a')
                    formatted_date = session_datetime.strftime('%b %d')
                    
                    next_appointment = {
                        'id': scheduler_session.id,
                        'date': formatted_date,
                        'day': day_name,
                        'date_full': scheduler_session.session_date.isoformat(),
                        'start_time': scheduler_session.start_time.strftime('%I:%M %p'),
                        'end_time': scheduler_session.end_time.strftime('%I:%M %p'),
                        'time_range': f"{scheduler_session.start_time.strftime('%I:%M %p')} - {scheduler_session.end_time.strftime('%I:%M %p')}",
                        'therapist': scheduler_session.staff.name if scheduler_session.staff and hasattr(scheduler_session.staff, 'name') else (scheduler_session.staff.username if scheduler_session.staff else 'Not assigned'),
                        'therapist_id': scheduler_session.staff.id if scheduler_session.staff else None,
                        'session_type': 'scheduled'
                    }
                else:
                    # Fallback to therapy sessions
                    therapy_session = TherapySession.objects.filter(
                        client=client,
                        session_date__gte=today,
                        status__in=['scheduled', 'in_progress']
                    ).order_by('session_date', 'start_time').first()
                    
                    if therapy_session:
                        session_datetime = datetime.combine(therapy_session.session_date, therapy_session.start_time)
                        day_name = session_datetime.strftime('%a')
                        formatted_date = session_datetime.strftime('%b %d')
                        
                        next_appointment = {
                            'id': therapy_session.id,
                            'date': formatted_date,
                            'day': day_name,
                            'date_full': therapy_session.session_date.isoformat(),
                            'start_time': therapy_session.start_time.strftime('%I:%M %p'),
                            'end_time': therapy_session.end_time.strftime('%I:%M %p'),
                            'time_range': f"{therapy_session.start_time.strftime('%I:%M %p')} - {therapy_session.end_time.strftime('%I:%M %p')}",
                            'therapist': therapy_session.staff.name if therapy_session.staff and hasattr(therapy_session.staff, 'name') else (therapy_session.staff.username if therapy_session.staff else 'Not assigned'),
                            'therapist_id': therapy_session.staff.id if therapy_session.staff else None,
                            'session_type': 'therapy'
                        }
            except Exception as e:
                import logging
                logging.error(f"Error fetching next appointment: {str(e)}")
            
            # 3. LAST SESSION SUMMARY
            last_session_summary = None
            try:
                last_session = TherapySession.objects.filter(
                    client=client,
                    status='completed'
                ).order_by('-session_date', '-start_time').first()
                
                if last_session:
                    # Get activities from last session
                    activities = Activity.objects.filter(session=last_session).values_list('activity_name', flat=True)
                    activity_names = [a for a in activities if a]  # Filter out None/empty
                    activity_summary = ', '.join(activity_names[:3]) if activity_names else 'Not specified'
                    
                    # Get goals met status
                    goals = GoalProgress.objects.filter(session=last_session)
                    total_goals = goals.count()
                    met_goals = goals.filter(is_met=True).count()
                    outcome = "Goal Completed" if met_goals > 0 else "In Progress"
                    
                    last_session_summary = {
                        'id': last_session.id,
                        'date': last_session.session_date.strftime('%b %d'),
                        'date_full': last_session.session_date.isoformat(),
                        'activity': activity_summary,
                        'outcome': outcome,
                        'goals_met': met_goals,
                        'total_goals': total_goals
                    }
            except Exception as e:
                import logging
                logging.error(f"Error fetching last session summary: {str(e)}")
            
            # 4. PROGRESS REPORT STATUS
            # Calculate progress report based on current quarter
            progress_report = None
            try:
                # Determine current quarter
                current_month = today.month
                if current_month in [1, 2, 3]:
                    quarter = 'Q1'
                    quarter_start = datetime(today.year, 1, 1).date()
                elif current_month in [4, 5, 6]:
                    quarter = 'Q2'
                    quarter_start = datetime(today.year, 4, 1).date()
                elif current_month in [7, 8, 9]:
                    quarter = 'Q3'
                    quarter_start = datetime(today.year, 7, 1).date()
                else:
                    quarter = 'Q4'
                    quarter_start = datetime(today.year, 10, 1).date()
                
                # Get treatment plans for this client
                treatment_plans = TreatmentPlan.objects.filter(
                    Q(client_id=str(client.id)) |
                    Q(client_id=client.username) |
                    Q(client_id=getattr(client, 'staff_id', '')) |
                    Q(client_name__icontains=client.name if hasattr(client, 'name') and client.name else '')
                )
                
                # Get goals from treatment plans
                treatment_goals = TreatmentGoal.objects.filter(treatment_plan__in=treatment_plans)
                total_goals = treatment_goals.count()
                achieved_goals = treatment_goals.filter(is_achieved=True).count()
                
                # Get sessions in this quarter
                quarter_sessions = TherapySession.objects.filter(
                    client=client,
                    session_date__gte=quarter_start,
                    session_date__lte=today,
                    status='completed'
                )
                
                progress_report = {
                    'report_name': f'Progress Report: {quarter}',
                    'quarter': quarter,
                    'status': 'Now Available',
                    'goals_achieved': achieved_goals,
                    'total_goals': total_goals,
                    'goals_achieved_display': f'{achieved_goals}/{total_goals}',
                    'sessions_in_quarter': quarter_sessions.count()
                }
            except Exception as e:
                import logging
                logging.error(f"Error calculating progress report: {str(e)}")
            
            # 5. SESSION ATTENDANCE OVERVIEW
            attendance_overview = None
            try:
                # Get all sessions for this client
                all_sessions = TherapySession.objects.filter(client=client)
                total_sessions = all_sessions.count()
                completed_sessions = all_sessions.filter(status='completed').count()
                cancelled_sessions = all_sessions.filter(status='cancelled').count()
                
                # Calculate attended rate
                attended_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
                
                # Get missed sessions (scheduled but not completed, excluding recent future ones)
                missed_sessions = all_sessions.filter(
                    status='cancelled',
                    session_date__lt=today  # Only count past cancelled sessions as missed
                ).count()
                
                # Cancellations with late notice (cancelled on the same day or after start time)
                late_cancellations = all_sessions.filter(
                    status='cancelled',
                    session_date=today
                ).count()
                
                attendance_overview = {
                    'attended_rate': round(attended_rate, 0),
                    'attended_rate_display': f'{int(round(attended_rate, 0))}%',
                    'missed_sessions': missed_sessions,
                    'missed_sessions_display': f'Missed: {missed_sessions} Sessions',
                    'late_cancellations': late_cancellations,
                    'late_cancellations_display': f'Cancellations With Late Notice: {late_cancellations}',
                    'total_scheduled': total_sessions,
                    'completed': completed_sessions,
                    'cancelled': cancelled_sessions
                }
            except Exception as e:
                import logging
                logging.error(f"Error calculating attendance overview: {str(e)}")
            
            # 6. TREATMENT PLAN
            treatment_plan_info = None
            try:
                # Get the most recent treatment plan
                latest_plan = TreatmentPlan.objects.filter(
                    Q(client_id=str(client.id)) |
                    Q(client_id=client.username) |
                    Q(client_id=getattr(client, 'staff_id', '')) |
                    Q(client_name__icontains=client.name if hasattr(client, 'name') and client.name else '')
                ).order_by('-created_at').first()
                
                if latest_plan:
                    # Format plan name based on plan type and quarter
                    plan_type_display = latest_plan.get_plan_type_display()
                    plan_name = f"Plan: {plan_type_display}"
                    
                    # Try to extract quarter from name or use current
                    if 'Q' in latest_plan.client_name:
                        quarter_match = latest_plan.client_name.split('Q')[1].split()[0] if 'Q' in latest_plan.client_name else None
                        if quarter_match:
                            plan_name = f"Plan: Q{quarter_match} {plan_type_display}"
                    
                    treatment_plan_info = {
                        'id': latest_plan.id,
                        'plan_name': plan_name,
                        'created_by': latest_plan.bcba.name if hasattr(latest_plan.bcba, 'name') else latest_plan.bcba.username,
                        'created_by_id': latest_plan.bcba.id,
                        'last_updated': latest_plan.updated_at.strftime('%B %d, %Y'),
                        'last_updated_date': latest_plan.updated_at.date().isoformat(),
                        'status': latest_plan.status,
                        'plan_type': latest_plan.plan_type
                    }
            except Exception as e:
                import logging
                logging.error(f"Error fetching treatment plan: {str(e)}")
            
            # 7. OVERALL PROGRESS (Pie Chart Data)
            overall_progress = None
            try:
                # Get treatment plans for this client (reuse from progress report section if available)
                if 'treatment_plans' not in locals():
                    treatment_plans = TreatmentPlan.objects.filter(
                        Q(client_id=str(client.id)) |
                        Q(client_id=client.username) |
                        Q(client_id=getattr(client, 'staff_id', '')) |
                        Q(client_name__icontains=client.name if hasattr(client, 'name') and client.name else '')
                    )
                
                # Get treatment goals
                treatment_goals = TreatmentGoal.objects.filter(treatment_plan__in=treatment_plans)
                total_goals_count = treatment_goals.count()
                achieved_goals_count = treatment_goals.filter(is_achieved=True).count()
                in_progress_goals = total_goals_count - achieved_goals_count
                
                # Calculate Goal Mastery Rate (percentage of achieved goals)
                goal_mastery_rate = (achieved_goals_count / total_goals_count * 100) if total_goals_count > 0 else 0
                
                # Calculate Behavior Improvement (from incidents reduction)
                # Compare current period vs previous period
                current_period_start = today - timedelta(days=30)
                previous_period_start = current_period_start - timedelta(days=30)
                
                current_incidents = Incident.objects.filter(
                    session__client=client,
                    session__session_date__gte=current_period_start,
                    session__session_date__lt=today
                ).count()
                
                previous_incidents = Incident.objects.filter(
                    session__client=client,
                    session__session_date__gte=previous_period_start,
                    session__session_date__lt=current_period_start
                ).count()
                
                # Calculate improvement percentage
                if previous_incidents > 0:
                    behavior_improvement = ((previous_incidents - current_incidents) / previous_incidents * 100)
                    behavior_improvement = max(0, behavior_improvement)  # Don't show negative
                else:
                    behavior_improvement = 0 if current_incidents == 0 else 0
                
                # Calculate pie chart segments
                total_progress = goal_mastery_rate + behavior_improvement + (in_progress_goals * 10)  # Scale in_progress
                if total_progress == 0:
                    total_progress = 100  # Default to 100 for display
                
                goal_mastery_percentage = (goal_mastery_rate / total_progress * 100) if total_progress > 0 else 0
                behavior_improvement_percentage = (behavior_improvement / total_progress * 100) if total_progress > 0 else 0
                goals_in_progress_percentage = 100 - goal_mastery_percentage - behavior_improvement_percentage
                
                overall_progress = {
                    'pie_chart': {
                        'segments': [
                            {
                                'label': 'Goal Mastery Rate',
                                'value': round(goal_mastery_percentage, 1),
                                'color': 'green',
                                'percentage': round(goal_mastery_rate, 0)
                            },
                            {
                                'label': 'Behavior Improvement',
                                'value': round(behavior_improvement_percentage, 1),
                                'color': 'gold',
                                'percentage': round(behavior_improvement, 0)
                            },
                            {
                                'label': 'Goals in Progress',
                                'value': round(goals_in_progress_percentage, 1),
                                'color': 'white',
                                'count': in_progress_goals
                            }
                        ]
                    },
                    'legend': [
                        {
                            'label': 'Goal Mastery Rate',
                            'value': f'{round(goal_mastery_rate, 0)}%',
                            'color': 'green'
                        },
                        {
                            'label': 'Behavior Improvement',
                            'value': f'{round(behavior_improvement, 0)}%',
                            'color': 'gold'
                        },
                        {
                            'label': 'Goals in Progress',
                            'value': str(in_progress_goals),
                            'color': 'white'
                        }
                    ],
                    'summary': {
                        'goal_mastery_rate': round(goal_mastery_rate, 0),
                        'behavior_improvement': round(behavior_improvement, 0),
                        'goals_in_progress': in_progress_goals,
                        'total_goals': total_goals_count,
                        'achieved_goals': achieved_goals_count
                    }
                }
            except Exception as e:
                import logging
                logging.error(f"Error calculating overall progress: {str(e)}")
            
            # Prepare final response
            return Response({
                'welcome': welcome_data,
                'next_appointment': next_appointment,
                'last_session_summary': last_session_summary,
                'progress_report_status': progress_report,
                'session_attendance_overview': attendance_overview,
                'treatment_plan': treatment_plan_info,
                'overall_progress': overall_progress,
                'calculated_at': tz.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'message': 'Failed to retrieve client dashboard data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)