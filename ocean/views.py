# ocean/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatMessage, Alert
from .serializers import ChatMessageSerializer, AlertSerializer
from .utils import generate_ai_response, generate_ai_response_with_db_context
from django.shortcuts import get_object_or_404

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    #permission_classes = [IsAuthenticated]

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
