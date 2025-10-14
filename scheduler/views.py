from rest_framework import generics, permissions
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
            ).order_by('session_date', 'start_time') # ascending order
            
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
    # Only the assigned RBT can start
    if request.user != session.rbt:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    session.status = 'in_progress'
    session.save()

    # Create time tracker entry
    TimeTracker.objects.update_or_create(session=session, defaults={'start_time': timezone.now()})

    return JsonResponse({'message': 'Session started'})

def end_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.rbt:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    session.status = 'completed'
    session.save()

    tracker = TimeTracker.objects.get(session=session)
    tracker.end_time = timezone.now()
    tracker.save()

    # Update duration in Session
    session.duration_minutes = tracker.duration
    session.save()

    return JsonResponse({'message': 'Session ended', 'duration': tracker.duration})

def log_behavior(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.rbt:
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


