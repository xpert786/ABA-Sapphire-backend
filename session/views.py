from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from datetime import timedelta
import json

from .models import (
    Session, SessionTimer, AdditionalTime, PreSessionChecklist,
    Activity, ReinforcementStrategy, ABCEvent, GoalProgress,
    Incident, SessionNote, TimeTracker
)
from .serializers import (
    SessionListSerializer, SessionDetailSerializer, SessionCreateUpdateSerializer,
    SessionTimerSerializer, SessionTimerStartStopSerializer,
    AdditionalTimeSerializer, PreSessionChecklistSerializer,
    ActivitySerializer, ReinforcementStrategySerializer,
    ABCEventSerializer, GoalProgressSerializer,
    IncidentSerializer, SessionNoteSerializer,
    SessionSubmitSerializer, SessionPreviewSerializer,
    TimeTrackerSerializer, TimeTrackerCreateSerializer, TimeTrackerUpdateSerializer
)

class SessionListView(generics.ListCreateAPIView):
    """API view for listing and creating sessions"""
    serializer_class = SessionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Session.objects.select_related('client', 'staff')
        
        # Role-based access control
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if role_name in ['Admin', 'Superadmin']:
                # Admin can see all sessions
                pass
            elif role_name in ['RBT', 'BCBA']:
                # Staff can see sessions they're assigned to
                queryset = queryset.filter(staff=user)
            elif role_name == 'Clients/Parent':
                # Clients can see their own sessions
                queryset = queryset.filter(client=user)
        else:
            # Default: users can only see their own sessions
            queryset = queryset.filter(staff=user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)
        
        # Filter by client if provided (admin only)
        client_filter = self.request.query_params.get('client_id')
        if client_filter and hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            if role_name in ['Admin', 'Superadmin']:
                queryset = queryset.filter(client_id=client_filter)
        
        # Filter by staff if provided (admin only)
        staff_filter = self.request.query_params.get('staff_id')
        if staff_filter and hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            if role_name in ['Admin', 'Superadmin']:
                queryset = queryset.filter(staff_id=staff_filter)
            
        return queryset.order_by('-session_date', '-start_time')

    def perform_create(self, serializer):
        serializer.save(staff=self.request.user)

class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating, and deleting sessions"""
    serializer_class = SessionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Session.objects.select_related('client', 'staff').prefetch_related(
            'timer', 'additional_times', 'checklist_items', 'activities',
            'reinforcement_strategies', 'abc_events', 'goal_progress',
            'incidents', 'notes'
        )
        
        # Filter based on user role
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if role_name in ['RBT', 'BCBA']:
                queryset = queryset.filter(staff=user)
            elif role_name == 'Clients/Parent':
                queryset = queryset.filter(client=user)
                
        return queryset

class SessionTimerView(APIView):
    """API view for managing session timer"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        
        # Check permissions
        if not self._has_permission(request.user, session):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        timer, created = SessionTimer.objects.get_or_create(session=session)
        serializer = SessionTimerSerializer(timer)
        return Response(serializer.data)
    
    def post(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        
        # Check permissions
        if not self._has_permission(request.user, session):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SessionTimerStartStopSerializer(data=request.data)
        if serializer.is_valid():
            timer, created = SessionTimer.objects.get_or_create(session=session)
            action = serializer.validated_data['action']
            
            if action == 'start':
                if not timer.is_running:
                    timer.start_time = timezone.now()
                    timer.is_running = True
                    session.status = 'in_progress'
                    session.save()
            elif action == 'stop':
                if timer.is_running:
                    timer.end_time = timezone.now()
                    timer.is_running = False
                    if timer.start_time:
                        elapsed = timer.end_time - timer.start_time
                        timer.total_duration += elapsed
                    session.status = 'completed'
                    session.save()
            
            timer.save()
            return Response(SessionTimerSerializer(timer).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _has_permission(self, user, session):
        """Check if user has permission to manage this session"""
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            # Admin and Superadmin can access all sessions
            if role_name in ['Admin', 'Superadmin']:
                return True
            return (role_name in ['RBT', 'BCBA'] and session.staff == user) or \
                   (role_name == 'Clients/Parent' and session.client == user)
        return False

class AdditionalTimeView(generics.ListCreateAPIView):
    """API view for managing additional time entries"""
    serializer_class = AdditionalTimeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return AdditionalTime.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class PreSessionChecklistView(generics.ListCreateAPIView):
    """API view for managing pre-session checklist"""
    serializer_class = PreSessionChecklistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return PreSessionChecklist.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class ActivityView(generics.ListCreateAPIView):
    """API view for managing session activities"""
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return Activity.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class ReinforcementStrategyView(generics.ListCreateAPIView):
    """API view for managing reinforcement strategies"""
    serializer_class = ReinforcementStrategySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return ReinforcementStrategy.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class ABCEventView(generics.ListCreateAPIView):
    """API view for managing ABC events"""
    serializer_class = ABCEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return ABCEvent.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class GoalProgressView(generics.ListCreateAPIView):
    """API view for managing goal progress"""
    serializer_class = GoalProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return GoalProgress.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class IncidentView(generics.ListCreateAPIView):
    """API view for managing incidents"""
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return Incident.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

class SessionNoteView(generics.ListCreateAPIView):
    """API view for managing session notes"""
    serializer_class = SessionNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        return SessionNote.objects.filter(session_id=session_id)
    
    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        serializer.save(session=session)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_session(request):
    """API endpoint for submitting session data"""
    serializer = SessionSubmitSerializer(data=request.data)
    if serializer.is_valid():
        session_id = serializer.validated_data['session_id']
        submit_type = serializer.validated_data['submit_type']
        
        session = get_object_or_404(Session, id=session_id)
        
        # Check permissions
        if not (hasattr(request.user, 'role') and request.user.role and 
                request.user.role.name in ['RBT', 'BCBA'] and session.staff == request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if submit_type == 'submit':
            session.status = 'completed'
            session.save()
            
            return Response({
                'message': 'Session submitted successfully',
                'session_id': session_id,
                'status': 'completed'
            })
        else:
            return Response({
                'message': 'Session saved as draft',
                'session_id': session_id,
                'status': session.status
            })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def preview_session(request):
    """API endpoint for previewing session data"""
    serializer = SessionPreviewSerializer(data=request.data)
    if serializer.is_valid():
        session_id = serializer.validated_data['session_id']
        session = get_object_or_404(Session, id=session_id)
        
        # Check permissions
        if not (hasattr(request.user, 'role') and request.user.role and 
                request.user.role.name in ['RBT', 'BCBA'] and session.staff == request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        session_serializer = SessionDetailSerializer(session)
        return Response(session_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upcoming_sessions(request):
    """API endpoint for getting upcoming sessions"""
    user = request.user
    queryset = Session.objects.select_related('client', 'staff').filter(
        session_date__gte=timezone.now().date(),
        status__in=['scheduled', 'in_progress']
    )
    
    # Role-based access control
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name in ['Admin', 'Superadmin']:
            # Admin can see all upcoming sessions
            pass
        elif role_name in ['RBT', 'BCBA']:
            queryset = queryset.filter(staff=user)
        elif role_name == 'Clients/Parent':
            queryset = queryset.filter(client=user)
    else:
        # Default: users can only see their own sessions
        queryset = queryset.filter(staff=user)
    
    serializer = SessionListSerializer(queryset.order_by('session_date', 'start_time'), many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def session_statistics(request):
    """API endpoint for getting session statistics"""
    user = request.user
    queryset = Session.objects.all()
    
    # Role-based access control
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name in ['Admin', 'Superadmin']:
            # Admin can see all sessions
            pass
        elif role_name in ['RBT', 'BCBA']:
            queryset = queryset.filter(staff=user)
        elif role_name == 'Clients/Parent':
            queryset = queryset.filter(client=user)
    else:
        # Default: users can only see their own sessions
        queryset = queryset.filter(staff=user)
    
    # Filter by date range if provided
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date:
        queryset = queryset.filter(session_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(session_date__lte=end_date)
    
    # Calculate statistics
    total_sessions = queryset.count()
    completed_sessions = queryset.filter(status='completed').count()
    in_progress_sessions = queryset.filter(status='in_progress').count()
    scheduled_sessions = queryset.filter(status='scheduled').count()
    cancelled_sessions = queryset.filter(status='cancelled').count()
    
    # Calculate completion rate
    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Get recent sessions (last 7 days)
    from datetime import timedelta
    recent_date = timezone.now().date() - timedelta(days=7)
    recent_sessions = queryset.filter(session_date__gte=recent_date).count()
    
    return Response({
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'in_progress_sessions': in_progress_sessions,
        'scheduled_sessions': scheduled_sessions,
        'cancelled_sessions': cancelled_sessions,
        'completion_rate': round(completion_rate, 2),
        'recent_sessions_7_days': recent_sessions
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_sessions(request):
    """API endpoint for getting sessions for a specific user (admin only)"""
    user = request.user
    
    # Check if user is admin
    if not (hasattr(user, 'role') and user.role and 
            user.role.name in ['Admin', 'Superadmin']):
        return Response(
            {'error': 'Only administrators can access user sessions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get user_id from query params
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response(
            {'error': 'user_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get sessions for the target user
    queryset = Session.objects.select_related('client', 'staff').filter(
        models.Q(staff_id=user_id) | models.Q(client_id=user_id)
    )
    
    # Filter by status if provided
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Filter by date range if provided
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date:
        queryset = queryset.filter(session_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(session_date__lte=end_date)
    
    serializer = SessionListSerializer(queryset.order_by('-session_date', '-start_time'), many=True)
    
    return Response({
        'user': {
            'id': target_user.id,
            'username': target_user.username,
            'name': target_user.get_full_name() or target_user.username,
            'role': target_user.role.name if hasattr(target_user, 'role') and target_user.role else 'No role'
        },
        'sessions': serializer.data,
        'total_sessions': queryset.count()
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_details(request, user_id):
    """API endpoint for getting detailed user information by ID"""
    current_user = request.user
    
    # Check permissions
    if hasattr(current_user, 'role') and current_user.role:
        role_name = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
        
        # Admin and Superadmin can see any user details
        if role_name not in ['Admin', 'Superadmin']:
            # Regular users can only see their own details
            if current_user.id != int(user_id):
                return Response(
                    {'error': 'You can only view your own user details'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
    else:
        # Default: users can only see their own details
        if current_user.id != int(user_id):
            return Response(
                {'error': 'You can only view your own user details'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = User.objects.select_related('role').get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get user's sessions (as staff)
    staff_sessions = Session.objects.filter(staff=target_user).count()
    client_sessions = Session.objects.filter(client=target_user).count()
    
    # Get recent sessions (last 30 days)
    from datetime import timedelta
    recent_date = timezone.now().date() - timedelta(days=30)
    recent_staff_sessions = Session.objects.filter(
        staff=target_user, 
        session_date__gte=recent_date
    ).count()
    recent_client_sessions = Session.objects.filter(
        client=target_user, 
        session_date__gte=recent_date
    ).count()
    
    # Get user's role information
    role_info = None
    if hasattr(target_user, 'role') and target_user.role:
        # Handle permissions properly - convert to list if it's a ManyRelatedManager
        permissions = getattr(target_user.role, 'permissions', [])
        if hasattr(permissions, 'all'):
            permissions = [perm.name for perm in permissions.all()]
        elif hasattr(permissions, '__iter__') and not isinstance(permissions, str):
            permissions = list(permissions)
        else:
            permissions = []
            
        role_info = {
            'id': target_user.role.id,
            'name': target_user.role.name,
            'description': getattr(target_user.role, 'description', ''),
            'permissions': permissions
        }
    
    # Get user's profile information
    profile_info = {
        'first_name': target_user.first_name or '',
        'last_name': target_user.last_name or '',
        'email': target_user.email or '',
        'phone': getattr(target_user, 'phone', '') or '',
        'address': getattr(target_user, 'address', '') or '',
        'date_joined': target_user.date_joined.isoformat() if target_user.date_joined else None,
        'last_login': target_user.last_login.isoformat() if target_user.last_login else None,
        'is_active': target_user.is_active,
        'is_staff': target_user.is_staff,
        'is_superuser': target_user.is_superuser
    }
    
    # Get user's session statistics
    session_stats = {
        'total_sessions_as_staff': staff_sessions,
        'total_sessions_as_client': client_sessions,
        'recent_sessions_as_staff': recent_staff_sessions,
        'recent_sessions_as_client': recent_client_sessions,
        'total_sessions': staff_sessions + client_sessions
    }
    
    # Get upcoming sessions
    upcoming_sessions = Session.objects.filter(
        models.Q(staff=target_user) | models.Q(client=target_user),
        session_date__gte=timezone.now().date(),
        status__in=['scheduled', 'in_progress']
    ).count()
    
    try:
        # Ensure all data is JSON serializable
        response_data = {
            'user': {
                'id': int(target_user.id),
                'username': str(target_user.username),
                'profile': profile_info,
                'role': role_info,
                'session_statistics': session_stats,
                'upcoming_sessions': int(upcoming_sessions)
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to serialize user data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_bcba_clients(request):
    """API endpoint for BCBAs to get their client list"""
    user = request.user
    
    # Check if user is BCBA or has appropriate role
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        # Only BCBAs and admins can access this endpoint
        if role_name not in ['BCBA', 'Admin', 'Superadmin']:
            return Response(
                {'error': 'Only BCBAs and administrators can access client lists'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'User role not found'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Add debug parameter to show all clients for troubleshooting
    debug_mode = request.query_params.get('debug', 'false').lower() == 'true'
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get clients for this BCBA
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if role_name in ['Admin', 'Superadmin'] or debug_mode:
                # Admin can see all clients, or debug mode shows all clients
                clients = User.objects.filter(
                    role__name__in=['Clients/Parent', 'Client']
                ).select_related('role').order_by('first_name', 'last_name')
            else:
                # BCBA can see clients assigned to them
                # First try to get clients assigned via supervisor field
                clients = User.objects.filter(
                    supervisor=user,
                    role__name__in=['Clients/Parent', 'Client']
                ).select_related('role').order_by('first_name', 'last_name')
                
                # Debug: Check if supervisor field exists and has clients
                supervisor_clients_count = clients.count()
                
                # If no clients found via supervisor field, fall back to session history
                if not clients.exists():
                    client_ids = Session.objects.filter(staff=user).values_list('client_id', flat=True).distinct()
                    clients = User.objects.filter(
                        id__in=client_ids,
                        role__name__in=['Clients/Parent', 'Client']
                    ).select_related('role').order_by('first_name', 'last_name')
                    
                    # Debug: Check session-based clients
                    session_clients_count = clients.count()
                    
                    # If still no clients, try broader search for any clients
                    if not clients.exists():
                        # Try to find any clients with the role, regardless of assignment
                        all_clients = User.objects.filter(
                            role__name__in=['Clients/Parent', 'Client']
                        ).select_related('role').order_by('first_name', 'last_name')
                        
                        # For debugging, let's see what clients exist
                        debug_info = {
                            'supervisor_clients_count': supervisor_clients_count,
                            'session_clients_count': session_clients_count,
                            'total_clients_with_role': all_clients.count(),
                            'user_id': user.id,
                            'user_role': user.role.name if hasattr(user, 'role') and user.role else 'No role'
                        }
                        
                        # Return debug info if no clients found
                        if not all_clients.exists():
                            return Response({
                                'bcba': {
                                    'id': int(user.id),
                                    'username': str(user.username),
                                    'name': user.get_full_name() or user.username,
                                    'role': user.role.name if hasattr(user, 'role') and user.role else 'No role'
                                },
                                'clients': [],
                                'total_clients': 0,
                                'debug_info': debug_info,
                                'message': 'No clients found. Check if clients exist and have proper role assignments.'
                            })
                        else:
                            # Use all clients as fallback for debugging
                            clients = all_clients
        else:
            clients = User.objects.none()
        
        # Get additional client information
        client_list = []
        for client in clients:
            # Get session statistics for this client
            # Use the assigned BCBA relationship for more accurate data
            if hasattr(client, 'supervisor') and client.supervisor == user:
                # Client is directly assigned to this BCBA
                total_sessions = Session.objects.filter(client=client, staff=user).count()
                completed_sessions = Session.objects.filter(
                    client=client, 
                    staff=user, 
                    status='completed'
                ).count()
                
                # Get recent sessions (last 30 days)
                from datetime import timedelta
                recent_date = timezone.now().date() - timedelta(days=30)
                recent_sessions = Session.objects.filter(
                    client=client,
                    staff=user,
                    session_date__gte=recent_date
                ).count()
                
                # Get upcoming sessions
                upcoming_sessions = Session.objects.filter(
                    client=client,
                    staff=user,
                    session_date__gte=timezone.now().date(),
                    status__in=['scheduled', 'in_progress']
                ).count()
                
                # Get last session date
                last_session = Session.objects.filter(
                    client=client,
                    staff=user
                ).order_by('-session_date').first()
            else:
                # Fallback to session-based statistics
                total_sessions = Session.objects.filter(client=client, staff=user).count()
                completed_sessions = Session.objects.filter(
                    client=client, 
                    staff=user, 
                    status='completed'
                ).count()
                
                from datetime import timedelta
                recent_date = timezone.now().date() - timedelta(days=30)
                recent_sessions = Session.objects.filter(
                    client=client,
                    staff=user,
                    session_date__gte=recent_date
                ).count()
                
                upcoming_sessions = Session.objects.filter(
                    client=client,
                    staff=user,
                    session_date__gte=timezone.now().date(),
                    status__in=['scheduled', 'in_progress']
                ).count()
                
                last_session = Session.objects.filter(
                    client=client,
                    staff=user
                ).order_by('-session_date').first()
            
            # Check assignment status
            is_directly_assigned = hasattr(client, 'supervisor') and client.supervisor == user
            assignment_status = "directly_assigned" if is_directly_assigned else "session_based"
            
            client_info = {
                'id': int(client.id),
                'username': str(client.username),
                'first_name': client.first_name or '',
                'last_name': client.last_name or '',
                'email': client.email or '',
                'phone': getattr(client, 'phone', '') or '',
                'is_active': client.is_active,
                'date_joined': client.date_joined.isoformat() if client.date_joined else None,
                'last_login': client.last_login.isoformat() if client.last_login else None,
                'role': {
                    'id': client.role.id if hasattr(client, 'role') and client.role else None,
                    'name': client.role.name if hasattr(client, 'role') and client.role else 'No role'
                },
                'assignment_status': assignment_status,
                'is_directly_assigned': is_directly_assigned,
                'session_statistics': {
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'recent_sessions_30_days': recent_sessions,
                    'upcoming_sessions': upcoming_sessions,
                    'completion_rate': round((completed_sessions / total_sessions * 100), 2) if total_sessions > 0 else 0
                },
                'last_session_date': last_session.session_date.isoformat() if last_session else None,
                'last_session_status': last_session.status if last_session else None
            }
            client_list.append(client_info)
        
        # Add debug information to help troubleshoot
        debug_info = {
            'bcba_id': user.id,
            'bcba_role': user.role.name if hasattr(user, 'role') and user.role else 'No role',
            'clients_found': len(client_list),
            'supervisor_field_exists': hasattr(User.objects.first(), 'supervisor') if User.objects.exists() else False,
            'debug_mode': debug_mode,
            'all_users_count': User.objects.count(),
            'clients_with_role_count': User.objects.filter(role__name__in=['Clients/Parent', 'Client']).count(),
            'sessions_with_bcba_count': Session.objects.filter(staff=user).count()
        }
        
        return Response({
            'bcba': {
                'id': int(user.id),
                'username': str(user.username),
                'name': user.get_full_name() or user.username,
                'role': user.role.name if hasattr(user, 'role') and user.role else 'No role'
            },
            'clients': client_list,
            'total_clients': len(client_list),
            'debug_info': debug_info
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get client list: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class TimeTrackerView(generics.ListCreateAPIView):
    """API view for listing and creating time tracker entries"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TimeTrackerCreateSerializer
        return TimeTrackerSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = TimeTracker.objects.select_related('session', 'created_by').all()
        
        # Filter based on user role
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if role_name in ['RBT', 'BCBA']:
                # Staff can see time trackers for sessions they're assigned to
                queryset = queryset.filter(
                    models.Q(session__staff=user) | models.Q(created_by=user)
                )
            elif role_name == 'Clients/Parent':
                # Clients can see time trackers for their sessions
                queryset = queryset.filter(session__client=user)
        
        # Filter by session if provided
        session_id = self.request.query_params.get('session')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
            
        # Filter by time type if provided
        time_type = self.request.query_params.get('time_type')
        if time_type:
            queryset = queryset.filter(time_type=time_type)
            
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)
            
        return queryset.order_by('-start_time')

class TimeTrackerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating, and deleting time tracker entries"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TimeTrackerUpdateSerializer
        return TimeTrackerSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = TimeTracker.objects.select_related('session', 'created_by').all()
        
        # Filter based on user role
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if role_name in ['RBT', 'BCBA']:
                # Staff can manage time trackers for sessions they're assigned to or created by them
                queryset = queryset.filter(
                    models.Q(session__staff=user) | models.Q(created_by=user)
                )
            elif role_name == 'Clients/Parent':
                # Clients can view time trackers for their sessions
                queryset = queryset.filter(session__client=user)
        
        return queryset

    def perform_update(self, serializer):
        # Only allow updates by the creator or session staff
        user = self.request.user
        time_tracker = self.get_object()
        
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if not (time_tracker.created_by == user or 
                   (role_name in ['RBT', 'BCBA'] and time_tracker.session.staff == user)):
                raise permissions.PermissionDenied("You can only update time trackers you created or for sessions you're assigned to")
        
        serializer.save()

    def perform_destroy(self, instance):
        # Only allow deletion by the creator or session staff
        user = self.request.user
        
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if not (instance.created_by == user or 
                   (role_name in ['RBT', 'BCBA'] and instance.session.staff == user)):
                raise permissions.PermissionDenied("You can only delete time trackers you created or for sessions you're assigned to")
        
        instance.delete()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def time_tracker_summary(request):
    """API endpoint for getting time tracker summary statistics"""
    user = request.user
    queryset = TimeTracker.objects.all()
    
    # Filter based on user role
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name in ['RBT', 'BCBA']:
            queryset = queryset.filter(
                models.Q(session__staff=user) | models.Q(created_by=user)
            )
        elif role_name == 'Clients/Parent':
            queryset = queryset.filter(session__client=user)
    
    # Filter by date range if provided
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date:
        queryset = queryset.filter(start_time__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(start_time__date__lte=end_date)
    
    # Calculate summary statistics
    total_entries = queryset.count()
    total_duration = sum(entry.duration for entry in queryset)  # in minutes
    
    # Group by time type
    time_type_summary = {}
    for entry in queryset:
        time_type = entry.time_type
        if time_type not in time_type_summary:
            time_type_summary[time_type] = {
                'count': 0,
                'total_duration': 0,
                'display_name': entry.get_time_type_display()
            }
        time_type_summary[time_type]['count'] += 1
        time_type_summary[time_type]['total_duration'] += entry.duration
    
    return Response({
        'total_entries': total_entries,
        'total_duration_minutes': total_duration,
        'total_duration_hours': round(total_duration / 60, 2),
        'total_duration_display': f"{int(total_duration // 60):02d}:{int(total_duration % 60):02d}",
        'time_type_summary': time_type_summary
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_session_from_schedule(request):
    """
    API endpoint to start a new session from a scheduled appointment in the scheduler app.
    Automatically pulls client, staff, date, time from the schedule.
    
    Request body:
    {
        "schedule_id": 123,  # ID from scheduler.Session
        "location": "Clinic Room A",  # Optional
        "service_type": "ABA"  # Optional
    }
    
    Returns the created session with timer started.
    """
    schedule_id = request.data.get('schedule_id')
    
    if not schedule_id:
        return Response(
            {'error': 'schedule_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Import scheduler models
    try:
        from scheduler.models import Session as ScheduledSession
    except ImportError:
        return Response(
            {'error': 'Scheduler module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Get the scheduled session
    try:
        scheduled = ScheduledSession.objects.select_related('client', 'staff').get(id=schedule_id)
    except ScheduledSession.DoesNotExist:
        return Response(
            {'error': f'Scheduled session with ID {schedule_id} not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions - staff must be assigned to this session
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['Admin', 'Superadmin']:
            if role_name not in ['RBT', 'BCBA'] or scheduled.staff != user:
                return Response(
                    {'error': 'You can only start sessions assigned to you'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'error': 'Only staff members can start sessions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if session already exists for this schedule
    existing_session = Session.objects.filter(
        client=scheduled.client,
        staff=scheduled.staff,
        session_date=scheduled.session_date,
        start_time=scheduled.start_time,
        end_time=scheduled.end_time
    ).first()
    
    if existing_session:
        # Return existing session with timer info
        try:
            timer = existing_session.timer
            timer_data = SessionTimerSerializer(timer).data
        except:
            timer_data = None
            
        return Response(
            {
                'message': 'Session already started from this schedule',
                'session': SessionDetailSerializer(existing_session).data,
                'timer': timer_data,
                'schedule_id': schedule_id
            },
            status=status.HTTP_200_OK
        )
    
    # Create new session from schedule
    try:
        with transaction.atomic():
            # Create session
            new_session = Session.objects.create(
                client=scheduled.client,
                staff=scheduled.staff,
                session_date=scheduled.session_date,
                start_time=scheduled.start_time,
                end_time=scheduled.end_time,
                location=request.data.get('location', 'Not specified'),
                service_type=request.data.get('service_type', 'ABA'),
                status='in_progress',
                session_notes=scheduled.session_notes or ''
            )
            
            # Start timer automatically
            timer = SessionTimer.objects.create(
                session=new_session,
                start_time=timezone.now(),
                is_running=True
            )
            
            return Response({
                'message': 'Session started successfully from schedule',
                'session': SessionDetailSerializer(new_session).data,
                'timer': SessionTimerSerializer(timer).data,
                'schedule_id': schedule_id
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response(
            {'error': f'Failed to create session: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_session_data_and_generate_notes(request, session_id):
    """
    API endpoint to save session data to database AND generate AI notes in one call.
    Accepts activities, goals, ABC events, reinforcement strategies, incidents, and checklist.
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['Admin', 'Superadmin']:
            if role_name not in ['RBT', 'BCBA'] or session.staff != user:
                return Response(
                    {'error': 'You can only manage your own sessions'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'error': 'Only staff members can save session data'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    request_data = request.data
    saved_data = {}
    
    # Save activities
    if 'activities' in request_data:
        activities_saved = []
        for activity_data in request_data['activities']:
            activity = Activity.objects.create(
                session=session,
                activity_name=activity_data.get('name', ''),
                duration_minutes=activity_data.get('duration', 0),
                reinforcement_strategies=activity_data.get('description', ''),
                notes=activity_data.get('response', '')
            )
            activities_saved.append(activity.id)
        saved_data['activities'] = f"{len(activities_saved)} activities saved"
    
    # Save goals
    if 'goals' in request_data:
        goals_saved = []
        for goal_data in request_data['goals']:
            goal = GoalProgress.objects.create(
                session=session,
                goal_description=f"{goal_data.get('goal', '')}. Target: {goal_data.get('target', '')}. {goal_data.get('trials', 0)} trials, {goal_data.get('successes', 0)} successes ({goal_data.get('percentage', 0)}%)",
                is_met=goal_data.get('percentage', 0) >= 80,
                implementation_method='verbal',
                notes=goal_data.get('notes', '')
            )
            goals_saved.append(goal.id)
        saved_data['goals'] = f"{len(goals_saved)} goals saved"
    
    # Save ABC events
    if 'abc_events' in request_data:
        abc_saved = []
        for abc_data in request_data['abc_events']:
            abc_event = ABCEvent.objects.create(
                session=session,
                antecedent=abc_data.get('antecedent', ''),
                behavior=abc_data.get('behavior', ''),
                consequence=abc_data.get('consequence', '')
            )
            abc_saved.append(abc_event.id)
        saved_data['abc_events'] = f"{len(abc_saved)} ABC events saved"
    
    # Save reinforcement strategies
    if 'reinforcement_strategies' in request_data:
        strategies_saved = []
        for strategy_data in request_data['reinforcement_strategies']:
            strategy = ReinforcementStrategy.objects.create(
                session=session,
                strategy_type=strategy_data.get('type', ''),
                frequency=strategy_data.get('effectiveness', 5),
                pr_ratio=strategy_data.get('effectiveness', 5),
                notes=strategy_data.get('description', '') + ' ' + strategy_data.get('notes', '')
            )
            strategies_saved.append(strategy.id)
        saved_data['reinforcement_strategies'] = f"{len(strategies_saved)} strategies saved"
    
    # Save incidents
    if 'incidents' in request_data:
        incidents_saved = []
        for incident_data in request_data['incidents']:
            incident = Incident.objects.create(
                session=session,
                incident_type=incident_data.get('type', 'minor_disruption'),
                behavior_severity=incident_data.get('severity', 'low'),
                start_time=timezone.now(),
                duration_minutes=incident_data.get('duration', 0),
                description=incident_data.get('description', '')
            )
            incidents_saved.append(incident.id)
        saved_data['incidents'] = f"{len(incidents_saved)} incidents saved"
    
    # Save checklist items
    if 'checklist' in request_data:
        checklist_data = request_data['checklist']
        checklist_saved = []
        
        if checklist_data.get('materials_ready'):
            PreSessionChecklist.objects.create(
                session=session,
                item_name='Materials Ready',
                is_completed=True,
                notes=checklist_data.get('notes', '')
            )
            checklist_saved.append('materials_ready')
        
        if checklist_data.get('environment_prepared'):
            PreSessionChecklist.objects.create(
                session=session,
                item_name='Environment Prepared',
                is_completed=True,
                notes=''
            )
            checklist_saved.append('environment_prepared')
        
        if checklist_data.get('reviewed_goals'):
            PreSessionChecklist.objects.create(
                session=session,
                item_name='Goals Reviewed',
                is_completed=True,
                notes=''
            )
            checklist_saved.append('reviewed_goals')
        
        saved_data['checklist'] = f"{len(checklist_saved)} checklist items saved"
    
    # Now generate AI notes using the saved data
    try:
        from ocean.utils import generate_session_notes
        
        # Collect all data from database (including what we just saved)
        session_data = {}
        
        # Basic session info
        session_data['session_info'] = {
            'client': session.client.name if hasattr(session.client, 'name') else session.client.username,
            'staff': session.staff.name if hasattr(session.staff, 'name') else session.staff.username,
            'date': str(session.session_date),
            'start_time': str(session.start_time),
            'end_time': str(session.end_time),
            'location': session.location or 'Not specified',
            'service_type': session.service_type or 'ABA',
            'status': session.status
        }
        
        # Get all related data from database
        session_data['activities'] = [
            {
                'name': a.activity_name,
                'duration': a.duration_minutes,
                'description': a.reinforcement_strategies,
                'response': a.notes or ''
            }
            for a in session.activities.all()
        ]
        
        session_data['goals'] = [
            {
                'goal': g.goal_description,
                'is_met': g.is_met,
                'implementation': g.implementation_method,
                'notes': g.notes or ''
            }
            for g in session.goal_progress.all()
        ]
        
        session_data['abc_events'] = [
            {
                'antecedent': e.antecedent,
                'behavior': e.behavior,
                'consequence': e.consequence
            }
            for e in session.abc_events.all()
        ]
        
        session_data['reinforcement_strategies'] = [
            {
                'type': s.strategy_type,
                'frequency': s.frequency,
                'pr_ratio': s.pr_ratio,
                'notes': s.notes
            }
            for s in session.reinforcement_strategies.all()
        ]
        
        session_data['incidents'] = [
            {
                'type': i.incident_type,
                'severity': i.behavior_severity,
                'description': i.description
            }
            for i in session.incidents.all()
        ]
        
        # Generate AI notes
        ai_notes = generate_session_notes(session_data)
        
        # Save notes if requested
        auto_save = request_data.get('auto_save', True)
        if auto_save and not ai_notes.startswith('AI error'):
            session.session_notes = ai_notes
            session.save()
        
        return Response({
            'session_id': session.id,
            'saved_data': saved_data,
            'generated_notes': ai_notes,
            'auto_saved': auto_save and not ai_notes.startswith('AI error'),
            'message': 'Session data saved to database and AI notes generated successfully'
        })
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available', 'saved_data': saved_data}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to generate notes: {str(e)}', 'saved_data': saved_data}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_session_dashboard_with_ocean(request, session_id):
    """
    Get comprehensive session dashboard with Ocean AI integration
    Includes prompts, note flow status, and session validation
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['Admin', 'Superadmin']:
            if role_name not in ['RBT', 'BCBA'] or session.staff != user:
                return Response(
                    {'error': 'You can only access your own sessions'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'error': 'Only staff members can access session dashboard'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Import Ocean models and functions
        from ocean.models import SessionPrompt, SessionNoteFlow
        from ocean.utils import generate_session_notes
        
        # Get or create note flow
        note_flow, created = SessionNoteFlow.objects.get_or_create(session=session)
        
        # Get all prompts for this session
        prompts = SessionPrompt.objects.filter(session=session).order_by('-created_at')
        
        # Get session timing info
        now = timezone.now().time()
        session_end = session.end_time
        time_remaining = 0
        if now < session_end:
            time_remaining = (session_end.hour * 60 + session_end.minute) - (now.hour * 60 + now.minute)
        
        # Check if in final 15 minutes
        in_final_15_minutes = time_remaining <= 15 and time_remaining > 0
        
        # Get pending prompts
        pending_prompts = prompts.filter(is_responded=False)
        
        # Check session end eligibility
        can_end_session = note_flow.final_note_submitted
        
        # Get session data for AI note generation
        session_data = {
            'session_info': {
                'client': session.client.name if hasattr(session.client, 'name') else session.client.username,
                'staff': session.staff.name if hasattr(session.staff, 'name') else session.staff.username,
                'date': str(session.session_date),
                'start_time': str(session.start_time),
                'end_time': str(session.end_time),
                'location': session.location or 'Not specified',
                'service_type': session.service_type or 'ABA',
                'status': session.status
            },
            'activities': [
                {
                    'name': a.activity_name,
                    'duration': a.duration_minutes,
                    'description': a.reinforcement_strategies,
                    'response': a.notes or ''
                }
                for a in session.activities.all()
            ],
            'goals': [
                {
                    'goal': g.goal_description,
                    'is_met': g.is_met,
                    'implementation': g.implementation_method,
                    'notes': g.notes or ''
                }
                for g in session.goal_progress.all()
            ],
            'abc_events': [
                {
                    'antecedent': e.antecedent,
                    'behavior': e.behavior,
                    'consequence': e.consequence
                }
                for e in session.abc_events.all()
            ],
            'reinforcement_strategies': [
                {
                    'type': s.strategy_type,
                    'frequency': s.frequency,
                    'pr_ratio': s.pr_ratio,
                    'notes': s.notes
                }
                for s in session.reinforcement_strategies.all()
            ],
            'incidents': [
                {
                    'type': i.incident_type,
                    'severity': i.behavior_severity,
                    'description': i.description
                }
                for i in session.incidents.all()
            ]
        }
        
        return Response({
            'session': {
                'id': session.id,
                'client': session.client.name if hasattr(session.client, 'name') else session.client.username,
                'date': session.session_date,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'status': session.status,
                'time_remaining_minutes': time_remaining,
                'in_final_15_minutes': in_final_15_minutes
            },
            'ocean_integration': {
                'note_flow': {
                    'is_note_completed': note_flow.is_note_completed,
                    'final_note_submitted': note_flow.final_note_submitted,
                    'ai_generated_note': note_flow.ai_generated_note,
                    'rbt_reviewed': note_flow.rbt_reviewed
                },
                'prompts': {
                    'total': prompts.count(),
                    'responded': prompts.filter(is_responded=True).count(),
                    'pending': pending_prompts.count(),
                    'list': [
                        {
                            'id': p.id,
                            'type': p.prompt_type,
                            'message': p.message,
                            'response': p.response,
                            'is_responded': p.is_responded,
                            'created_at': p.created_at,
                            'responded_at': p.responded_at
                        }
                        for p in prompts
                    ]
                },
                'can_end_session': can_end_session,
                'blocking_reasons': _get_blocking_reasons(note_flow, pending_prompts),
                'recommendations': _get_session_recommendations(note_flow, prompts, time_remaining)
            },
            'session_data_summary': {
                'activities_count': len(session_data['activities']),
                'goals_count': len(session_data['goals']),
                'abc_events_count': len(session_data['abc_events']),
                'incidents_count': len(session_data['incidents'])
            }
        })
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to get session dashboard: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_ocean_prompt(request, session_id):
    """
    Create an Ocean AI prompt for the session
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['RBT', 'BCBA'] or session.staff != user:
            return Response(
                {'error': 'You can only create prompts for your own sessions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'Only staff members can create prompts'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from ocean.models import SessionPrompt
        
        prompt_type = request.data.get('prompt_type', 'engagement')
        
        # Define prompt messages based on type
        prompt_messages = {
            'engagement': "How is the session going? Are you hitting your targets today?",
            'goal_check': "How are the client's goals progressing? Any notable achievements?",
            'behavior_tracking': "Any significant behaviors to note? How is the client responding?",
            'note_reminder': "Don't forget to document key observations for your session note.",
            'session_wrap': "Here's what I've reviewed — would you like me to wrap up and generate your session note?"
        }
        
        message = prompt_messages.get(prompt_type, prompt_messages['engagement'])
        
        # Create the prompt
        prompt = SessionPrompt.objects.create(
            session=session,
            prompt_type=prompt_type,
            message=message
        )
        
        return Response({
            'prompt': {
                'id': prompt.id,
                'type': prompt.prompt_type,
                'message': prompt.message,
                'is_responded': prompt.is_responded,
                'created_at': prompt.created_at
            },
            'message': 'Ocean prompt created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to create prompt: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def respond_to_ocean_prompt(request, session_id, prompt_id):
    """
    Respond to an Ocean AI prompt
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['RBT', 'BCBA'] or session.staff != user:
            return Response(
                {'error': 'You can only respond to prompts for your own sessions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'Only staff members can respond to prompts'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from ocean.models import SessionPrompt
        
        prompt = get_object_or_404(SessionPrompt, id=prompt_id, session=session)
        response_text = request.data.get('response', '').strip()
        
        if not response_text:
            return Response(
                {'error': 'Response is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prompt.response = response_text
        prompt.is_responded = True
        prompt.responded_at = timezone.now()
        prompt.save()
        
        return Response({
            'prompt': {
                'id': prompt.id,
                'type': prompt.prompt_type,
                'message': prompt.message,
                'response': prompt.response,
                'is_responded': prompt.is_responded,
                'responded_at': prompt.responded_at
            },
            'message': 'Response submitted successfully'
        })
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to respond to prompt: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_ocean_ai_note(request, session_id):
    """
    Generate AI note using Ocean AI
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['RBT', 'BCBA'] or session.staff != user:
            return Response(
                {'error': 'You can only generate notes for your own sessions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'Only staff members can generate notes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from ocean.models import SessionNoteFlow
        from ocean.utils import generate_session_notes
        
        # Get or create note flow
        note_flow, created = SessionNoteFlow.objects.get_or_create(session=session)
        
        # Gather comprehensive session data
        session_data = {
            'session_info': {
                'client': session.client.name if hasattr(session.client, 'name') else session.client.username,
                'staff': session.staff.name if hasattr(session.staff, 'name') else session.staff.username,
                'date': str(session.session_date),
                'start_time': str(session.start_time),
                'end_time': str(session.end_time),
                'location': session.location or 'Not specified',
                'service_type': session.service_type or 'ABA',
                'status': session.status
            },
            'activities': [
                {
                    'name': a.activity_name,
                    'duration': a.duration_minutes,
                    'description': a.reinforcement_strategies,
                    'response': a.notes or ''
                }
                for a in session.activities.all()
            ],
            'goals': [
                {
                    'goal': g.goal_description,
                    'is_met': g.is_met,
                    'implementation': g.implementation_method,
                    'notes': g.notes or ''
                }
                for g in session.goal_progress.all()
            ],
            'abc_events': [
                {
                    'antecedent': e.antecedent,
                    'behavior': e.behavior,
                    'consequence': e.consequence
                }
                for e in session.abc_events.all()
            ],
            'reinforcement_strategies': [
                {
                    'type': s.strategy_type,
                    'frequency': s.frequency,
                    'pr_ratio': s.pr_ratio,
                    'notes': s.notes
                }
                for s in session.reinforcement_strategies.all()
            ],
            'incidents': [
                {
                    'type': i.incident_type,
                    'severity': i.behavior_severity,
                    'description': i.description
                }
                for i in session.incidents.all()
            ]
        }
        
        # Generate AI note
        ai_note = generate_session_notes(session_data)
        
        # Save AI note to note flow
        note_flow.ai_generated_note = ai_note
        note_flow.save()
        
        return Response({
            'ai_generated_note': ai_note,
            'session_data_summary': {
                'activities_count': len(session_data['activities']),
                'goals_count': len(session_data['goals']),
                'abc_events_count': len(session_data['abc_events']),
                'incidents_count': len(session_data['incidents'])
            },
            'message': 'AI note generated successfully'
        })
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to generate AI note: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def finalize_session_with_ocean(request, session_id):
    """
    Finalize session with Ocean AI note flow validation
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name not in ['RBT', 'BCBA'] or session.staff != user:
            return Response(
                {'error': 'You can only finalize your own sessions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'Only staff members can finalize sessions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from ocean.models import SessionNoteFlow
        
        # Get note flow
        note_flow, created = SessionNoteFlow.objects.get_or_create(session=session)
        
        # Check if note is completed
        if not note_flow.is_note_completed:
            return Response({
                'can_finalize': False,
                'error': 'Session note must be completed before finalizing',
                'required_actions': [
                    'Complete session note content',
                    'Review and finalize session note',
                    'Submit final session note'
                ],
                'note_flow_status': {
                    'is_note_completed': note_flow.is_note_completed,
                    'final_note_submitted': note_flow.final_note_submitted
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Finalize note flow
        note_flow.final_note_submitted = True
        note_flow.save()
        
        # Update session with final note
        if note_flow.ai_generated_note:
            session.session_notes = note_flow.ai_generated_note
        elif note_flow.note_content:
            session.session_notes = note_flow.note_content
        
        session.status = 'completed'
        session.save()
        
        return Response({
            'can_finalize': True,
            'message': 'Session finalized successfully',
            'note_flow_status': {
                'is_note_completed': note_flow.is_note_completed,
                'final_note_submitted': note_flow.final_note_submitted,
                'ai_generated_note': note_flow.ai_generated_note
            }
        })
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to finalize session: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_blocking_reasons(note_flow, pending_prompts):
    """Get detailed reasons why session cannot be ended"""
    reasons = []
    
    if not note_flow.is_note_completed:
        reasons.append("Session note is not completed")
    
    if not note_flow.final_note_submitted:
        reasons.append("Session note is not finalized")
    
    if pending_prompts.count() > 0:
        reasons.append(f"{pending_prompts.count()} pending prompts need responses")
    
    return reasons


def _get_session_recommendations(note_flow, prompts, time_remaining):
    """Get recommendations for the RBT based on session state"""
    recommendations = []
    
    if not note_flow.is_note_completed:
        recommendations.append("Complete your session note to document today's progress")
    
    if not note_flow.final_note_submitted:
        recommendations.append("Review and finalize your session note before ending")
    
    pending_prompts = prompts.filter(is_responded=False)
    if pending_prompts.exists():
        recommendations.append(f"Respond to {pending_prompts.count()} pending prompts")
    
    if time_remaining <= 15 and time_remaining > 0:
        recommendations.append("Session ending soon - consider wrapping up activities")
    
    if time_remaining <= 0:
        recommendations.append("Session time has ended - complete your notes and end session")
    
    return recommendations


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_ai_session_notes(request, session_id):
    """
    API endpoint to generate comprehensive session notes using Ocean AI (GPT-4).
    Collects all session data (activities, goals, behaviors, etc.) and generates
    professional, detailed session notes automatically.
    """
    # Get the session
    session = get_object_or_404(Session, id=session_id)
    
    # Check permissions - only staff can generate notes
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        # Admin/Superadmin can generate for any session
        if role_name not in ['Admin', 'Superadmin']:
            # Staff must be assigned to this session
            if role_name not in ['RBT', 'BCBA'] or session.staff != user:
                return Response(
                    {'error': 'You can only generate notes for your own sessions'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'error': 'Only staff members can generate session notes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if session data is provided in request body (manual mode)
    # Otherwise, collect from database (auto mode)
    request_data = request.data
    
    # If activities, goals, etc. are provided in request body, use them
    if any(key in request_data for key in ['activities', 'goals', 'abc_events', 'reinforcement_strategies', 'incidents', 'checklist']):
        # Manual mode - use provided data
        session_data = {}
        
        # Basic session info (always from database)
        session_data['session_info'] = {
            'client': session.client.name if hasattr(session.client, 'name') else session.client.username,
            'staff': session.staff.name if hasattr(session.staff, 'name') else session.staff.username,
            'date': str(session.session_date),
            'start_time': str(session.start_time),
            'end_time': str(session.end_time),
            'location': session.location or 'Not specified',
            'service_type': session.service_type or 'ABA',
            'status': session.status
        }
        
        # Use provided data from request body
        session_data['activities'] = request_data.get('activities', [])
        session_data['goals'] = request_data.get('goals', [])
        session_data['abc_events'] = request_data.get('abc_events', [])
        session_data['reinforcement_strategies'] = request_data.get('reinforcement_strategies', [])
        session_data['incidents'] = request_data.get('incidents', [])
        session_data['checklist'] = request_data.get('checklist', {})
        
        # Timer data (always from database if available)
        try:
            timer = session.timer
            session_data['timer'] = {
                'total_duration': str(timer.total_duration),
                'is_running': timer.is_running
            }
        except:
            session_data['timer'] = {'total_duration': 'Not tracked', 'is_running': False}
    else:
        # Auto mode - collect all session data from database
        session_data = {}
        
        # 1. Basic session info
        session_data['session_info'] = {
            'client': session.client.name if hasattr(session.client, 'name') else session.client.username,
            'staff': session.staff.name if hasattr(session.staff, 'name') else session.staff.username,
            'date': str(session.session_date),
            'start_time': str(session.start_time),
            'end_time': str(session.end_time),
            'location': session.location or 'Not specified',
            'service_type': session.service_type or 'ABA',
            'status': session.status
        }
        
        # 2. Timer data
        try:
            timer = session.timer
            session_data['timer'] = {
                'total_duration': str(timer.total_duration),
                'is_running': timer.is_running
            }
        except:
            session_data['timer'] = {'total_duration': 'Not tracked', 'is_running': False}
        
        # 3. Activities
        activities = session.activities.all()
        session_data['activities'] = [
            {
                'name': activity.activity_name,
                'duration': activity.duration_minutes,
                'description': activity.description or '',
                'response': activity.client_response or ''
            }
            for activity in activities
        ]
        
        # 4. Goal Progress
        goals = session.goal_progress.all()
        session_data['goals'] = [
            {
                'goal': goal.goal_name,
                'target': goal.target_behavior or '',
                'trials': goal.trials_completed,
                'successes': goal.successful_trials,
                'percentage': round((goal.successful_trials / goal.trials_completed * 100), 1) if goal.trials_completed > 0 else 0,
                'notes': goal.notes or ''
            }
            for goal in goals
        ]
        
        # 5. ABC Events (Behaviors)
        abc_events = session.abc_events.all()
        session_data['abc_events'] = [
            {
                'time': str(event.time),
                'antecedent': event.antecedent,
                'behavior': event.behavior,
                'consequence': event.consequence,
                'notes': event.notes or ''
            }
            for event in abc_events
        ]
        
        # 6. Reinforcement Strategies
        reinforcement = session.reinforcement_strategies.all()
        session_data['reinforcement_strategies'] = [
            {
                'type': strategy.strategy_type,
                'description': strategy.description or '',
                'effectiveness': strategy.effectiveness_rating,
                'notes': strategy.notes or ''
            }
            for strategy in reinforcement
        ]
        
        # 7. Incidents
        incidents = session.incidents.all()
        session_data['incidents'] = [
            {
                'type': incident.incident_type,
                'description': incident.description,
                'time': str(incident.time),
                'action_taken': incident.action_taken or ''
            }
            for incident in incidents
        ]
        
        # 8. Pre-session checklist
        try:
            checklist = session.checklist
            session_data['checklist'] = {
                'materials_ready': checklist.materials_ready,
                'environment_prepared': checklist.environment_prepared,
                'reviewed_goals': checklist.reviewed_goals,
                'notes': checklist.notes or ''
            }
        except:
            session_data['checklist'] = {}
    
    # Generate AI notes using Ocean AI
    try:
        from ocean.utils import generate_session_notes
        
        ai_notes = generate_session_notes(session_data)
        
        # Check if auto-save is requested
        auto_save = request.data.get('auto_save', False)
        
        if auto_save and not ai_notes.startswith('AI error'):
            # Save the notes to the session
            session.session_notes = ai_notes
            session.save()
        
        return Response({
            'session_id': session.id,
            'generated_notes': ai_notes,
            'session_data': session_data,
            'auto_saved': auto_save and not ai_notes.startswith('AI error'),
            'message': 'Session notes generated successfully using Ocean AI'
        })
        
    except ImportError:
        return Response(
            {'error': 'Ocean AI module not available'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to generate notes: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
