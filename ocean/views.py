# ocean/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatMessage, Alert, SessionPrompt, SessionNoteFlow
from .serializers import ChatMessageSerializer, AlertSerializer, SessionPromptSerializer, SessionNoteFlowSerializer
from .utils import generate_ai_response, generate_ai_response_with_db_context
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from session.models import Session

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ChatMessage.objects.all().order_by('-created_at')
        return ChatMessage.objects.filter(user=user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def send(self, request):
        message_text = request.data.get('message', '').strip()
        if not message_text:
            return Response({"detail": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Create chat instance but do not save yet
        chat = ChatMessage(user=request.user, message=message_text)

        # Generate AI response with database context
        ai_response = generate_ai_response_with_db_context(message_text, request.user)
        print("DEBUG AI response:", ai_response)  # check console

        chat.response = ai_response
        chat.save()  # save after assigning response

        return Response(ChatMessageSerializer(chat).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def context(self, request):
        """Get user context information for AI responses"""
        from .utils import build_user_context
        context = build_user_context(request.user)
        return Response({"context": context}, status=status.HTTP_200_OK)

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Alert.objects.filter(user=user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def my_alerts(self, request):
        alerts = Alert.objects.filter(user=request.user, is_read=False)
        return Response(AlertSerializer(alerts, many=True).data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        alert = get_object_or_404(Alert, pk=pk, user=request.user)
        alert.is_read = True
        alert.save()
        return Response(AlertSerializer(alert).data)

class SessionPromptViewSet(viewsets.ModelViewSet):
    """ViewSet for managing session prompts and interactions"""
    serializer_class = SessionPromptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name in ['RBT', 'BCBA']:
            return SessionPrompt.objects.filter(session__staff=user).order_by('-created_at')
        return SessionPrompt.objects.none()

    @action(detail=False, methods=['get'])
    def active_session_prompts(self, request):
        """Get active prompts for current session"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(Session, id=session_id, staff=request.user)
        prompts = SessionPrompt.objects.filter(session=session, is_responded=False)
        return Response(SessionPromptSerializer(prompts, many=True).data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a session prompt"""
        prompt = get_object_or_404(SessionPrompt, pk=pk, session__staff=request.user)
        response_text = request.data.get('response', '').strip()
        
        if not response_text:
            return Response({"detail": "response is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        prompt.response = response_text
        prompt.is_responded = True
        prompt.responded_at = timezone.now()
        prompt.save()
        
        return Response(SessionPromptSerializer(prompt).data)

    @action(detail=False, methods=['post'])
    def create_engagement_prompt(self, request):
        """Create an engagement check prompt for active session"""
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(Session, id=session_id, staff=request.user)
        
        # Create engagement prompt
        prompt = SessionPrompt.objects.create(
            session=session,
            prompt_type='engagement',
            message="How is the session going? Are you hitting your targets today?"
        )
        
        return Response(SessionPromptSerializer(prompt).data, status=status.HTTP_201_CREATED)

class SessionNoteFlowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing session note completion flow"""
    serializer_class = SessionNoteFlowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name in ['RBT', 'BCBA']:
            return SessionNoteFlow.objects.filter(session__staff=user).order_by('-created_at')
        return SessionNoteFlow.objects.none()

    @action(detail=False, methods=['get'])
    def session_note_status(self, request):
        """Get note completion status for a session"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(Session, id=session_id, staff=request.user)
        note_flow, created = SessionNoteFlow.objects.get_or_create(session=session)
        return Response(SessionNoteFlowSerializer(note_flow).data)

    @action(detail=False, methods=['post'])
    def start_note_flow(self, request):
        """Initialize note flow for a session"""
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(Session, id=session_id, staff=request.user)
        note_flow, created = SessionNoteFlow.objects.get_or_create(session=session)
        
        if not created:
            return Response({"detail": "Note flow already exists for this session"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(SessionNoteFlowSerializer(note_flow).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit_note(self, request, pk=None):
        """Submit session note content"""
        note_flow = get_object_or_404(SessionNoteFlow, pk=pk, session__staff=request.user)
        note_content = request.data.get('note_content', '').strip()
        
        if not note_content:
            return Response({"detail": "note_content is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        note_flow.note_content = note_content
        note_flow.is_note_completed = True
        note_flow.save()
        
        return Response(SessionNoteFlowSerializer(note_flow).data)

    @action(detail=True, methods=['post'])
    def generate_ai_note(self, request, pk=None):
        """Generate AI-assisted session note"""
        note_flow = get_object_or_404(SessionNoteFlow, pk=pk, session__staff=request.user)
        
        # Gather comprehensive session data
        session = note_flow.session
        session_data = self._gather_session_data(session)
        
        # Generate AI note using the comprehensive data
        ai_note = generate_session_notes(session_data)
        note_flow.ai_generated_note = ai_note
        note_flow.save()
        
        return Response({
            "ai_generated_note": ai_note,
            "message": "AI note generated successfully"
        })

    @action(detail=True, methods=['post'])
    def finalize_note(self, request, pk=None):
        """Finalize and submit the session note"""
        note_flow = get_object_or_404(SessionNoteFlow, pk=pk, session__staff=request.user)
        
        if not note_flow.is_note_completed:
            return Response({"detail": "Note must be completed before finalizing"}, status=status.HTTP_400_BAD_REQUEST)
        
        note_flow.final_note_submitted = True
        note_flow.save()
        
        # Update the session with the final note
        session = note_flow.session
        session.session_notes = note_flow.note_content
        session.save()
        
        return Response({
            "message": "Session note finalized and submitted successfully",
            "note_flow": SessionNoteFlowSerializer(note_flow).data
        })

    @action(detail=False, methods=['get'])
    def check_session_end_eligibility(self, request):
        """Check if session can be ended (requires completed note)"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(Session, id=session_id, staff=request.user)
        note_flow, created = SessionNoteFlow.objects.get_or_create(session=session)
        
        can_end = note_flow.final_note_submitted
        
        return Response({
            "can_end_session": can_end,
            "note_completed": note_flow.is_note_completed,
            "note_finalized": note_flow.final_note_submitted,
            "message": "Session can be ended" if can_end else "Session note must be completed before ending session"
        })

    @action(detail=False, methods=['get'])
    def get_session_wrap_prompt(self, request):
        """Get the 15-minute warning prompt for session wrap-up"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(Session, id=session_id, staff=request.user)
        
        # Check if we're in the last 15 minutes
        now = timezone.now().time()
        session_end = session.end_time
        
        # Calculate time remaining
        if now < session_end:
            time_remaining = (session_end.hour * 60 + session_end.minute) - (now.hour * 60 + now.minute)
            
            if time_remaining <= 15:
                # Create wrap-up prompt
                prompt = SessionPrompt.objects.create(
                    session=session,
                    prompt_type='session_wrap',
                    message="Here's what I've reviewed — would you like me to wrap up and generate your session note?"
                )
                
                return Response({
                    "show_prompt": True,
                    "time_remaining_minutes": time_remaining,
                    "prompt": SessionPromptSerializer(prompt).data,
                    "message": "Session is ending soon. Please complete your session note."
                })
        
        return Response({
            "show_prompt": False,
            "message": "Session is not yet in the final 15 minutes"
        })
