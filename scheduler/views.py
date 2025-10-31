from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from api.models import CustomUser
from .models import Session, TimeTracker, SessionLog
from .serializers import ClientSerializer, SessionSerializer
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
import logging
import sys

# Configure logging to handle Unicode properly
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Clients List - filtered by logged-in admin
class ClientListView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        admin_user = self.request.user
        if not admin_user.role:
            return CustomUser.objects.none()
        
        if admin_user.role.name == "Admin":
            return CustomUser.objects.filter(role__name="Clients/Parent", supervisor=admin_user).order_by('-id')
        else:
            return CustomUser.objects.none()

# Clients List - filtered by logged-in admin
class RBTListView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        admin_user = self.request.user
        if not admin_user.role:
            return CustomUser.objects.none()
        
        if admin_user.role.name == "Admin":
            return CustomUser.objects.filter(role__name="RBT", supervisor=admin_user).order_by('-id')
        else:
            return CustomUser.objects.none()


# Clients List - filtered by logged-in admin
class BCBAListView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        admin_user = self.request.user
        if not admin_user.role:
            return CustomUser.objects.none()
        
        if admin_user.role.name == "Admin":
            return CustomUser.objects.filter(role__name="BCBA", supervisor=admin_user).order_by('-id')
        else:
            return CustomUser.objects.none()

# Clients List - filtered by logged-in admin
class StaffListView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        admin_user = self.request.user
        if not admin_user.role:
            return CustomUser.objects.none()
        
        if admin_user.role.name == "Admin":
            return CustomUser.objects.filter(role__name__in=["BCBA", "RBT"], supervisor=admin_user).order_by('-id')
        else:
            return CustomUser.objects.none()

# Client Detail - retrieve a single client
class ClientDetailView(generics.RetrieveAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        admin_user = self.request.user
        if not admin_user.role:
            return CustomUser.objects.none()
        
        if admin_user.role.name == "Super Admin":
            return CustomUser.objects.filter(role__name="Client")
        elif admin_user.role.name == "Admin":
            return CustomUser.objects.filter(role__name="Client", supervisor=admin_user)
        else:
            return CustomUser.objects.none()

# Sessions List & Create
class SessionListCreateView(generics.ListCreateAPIView):
    queryset = Session.objects.all().order_by('-session_date')
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]  
    
    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        try:
            # Filter only sessions for the logged-in staff and only upcoming sessions
            queryset = Session.objects.filter(
                staff=user,
                session_date__gte=now.date()  # only future dates (including today)
            ).select_related('treatment_plan', 'client')
            
            # Filter by treatment_plan_id if provided
            treatment_plan_id = self.request.query_params.get('treatment_plan_id')
            if treatment_plan_id:
                queryset = queryset.filter(treatment_plan_id=treatment_plan_id)
            
            queryset = queryset.order_by('session_date', 'start_time') # ascending order
            
            # Test the queryset by converting to list to catch Unicode issues early
            list(queryset)
            return queryset
        except UnicodeEncodeError as e:
            logging.error(f"Unicode error in queryset: {e}")
            # Return empty queryset if Unicode error occurs
            return Session.objects.none()
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except UnicodeEncodeError as e:
            logging.error(f"Unicode encoding error: {e}")
            return JsonResponse({
                'error': 'Unicode encoding error occurred. Please check data for special characters.',
                'detail': str(e)
            }, status=500)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'detail': str(e)
            }, status=500)

# Session Detail - retrieve/update/delete a session
class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

def start_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    # Only the assigned staff can start
    if request.user != session.staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    session.status = 'in_progress'
    session.save()

    # Create time tracker entry
    TimeTracker.objects.update_or_create(session=session, defaults={'start_time': timezone.now()})

    return JsonResponse({'message': 'Session started'})

def end_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Check if session note is completed before allowing session to end
    from ocean.models import SessionNoteFlow
    try:
        note_flow = SessionNoteFlow.objects.get(session=session)
        if not note_flow.final_note_submitted:
            return JsonResponse({
                'error': 'Session note must be completed before ending session',
                'note_completed': note_flow.is_note_completed,
                'note_finalized': note_flow.final_note_submitted,
                'message': 'Please complete and finalize your session note before ending the session.'
            }, status=400)
    except SessionNoteFlow.DoesNotExist:
        return JsonResponse({
            'error': 'Session note flow not initialized',
            'message': 'Please start the session note flow before ending the session.'
        }, status=400)

    session.status = 'completed'
    session.save()

    # Update time tracker if it exists
    try:
        tracker = TimeTracker.objects.get(session=session)
        tracker.end_time = timezone.now()
        tracker.save()
        
        # Update duration in Session
        session.duration = tracker.duration
        session.save()
    except TimeTracker.DoesNotExist:
        pass

    return JsonResponse({
        'message': 'Session ended successfully', 
        'duration': getattr(tracker, 'duration', None) if 'tracker' in locals() else None
    })

def log_behavior(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    behavior = request.POST.get('behavior')
    antecedent = request.POST.get('antecedent')
    consequence = request.POST.get('consequence')
    reinforcement = request.POST.get('reinforcement')
    client_response = request.POST.get('client_response')

    SessionLog.objects.create(
        session=session,
        behavior=behavior,
        antecedent=antecedent,
        consequence=consequence,
        reinforcement=reinforcement,
        client_response=client_response
    )

    return JsonResponse({'message': 'Behavior logged successfully'})


