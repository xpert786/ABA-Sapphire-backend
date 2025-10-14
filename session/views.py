from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from datetime import timedelta

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
        
        # Filter based on user role
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
            
            if role_name in ['RBT', 'BCBA']:
                # Staff can see sessions they're assigned to
                queryset = queryset.filter(staff=user)
            elif role_name == 'Clients/Parent':
                # Clients can see their own sessions
                queryset = queryset.filter(client=user)
        
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
    
    # Filter based on user role
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        
        if role_name in ['RBT', 'BCBA']:
            queryset = queryset.filter(staff=user)
        elif role_name == 'Clients/Parent':
            queryset = queryset.filter(client=user)
    
    serializer = SessionListSerializer(queryset.order_by('session_date', 'start_time'), many=True)
    return Response(serializer.data)

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
