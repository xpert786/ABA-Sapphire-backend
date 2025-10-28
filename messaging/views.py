from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from django.shortcuts import get_object_or_404

User = get_user_model()

def get_private_room_name(user1_id, user2_id):
    return f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_private_chat(request):
    """
    Start or get a one-to-one chat room between two users
    """
    other_user_id = request.data.get('user_id')
    if not other_user_id:
        return Response({"error": "user_id is required"}, status=400)

    try:
        other_user = User.objects.get(id=other_user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    room_name = get_private_room_name(request.user.id, other_user.id)
    room, created = ChatRoom.objects.get_or_create(name=room_name)
    room.participants.set([request.user, other_user])
    room.save()

    serializer = ChatRoomSerializer(room)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request, room_id):
    """
    Send a message in a chat room
    """
    content = request.data.get('content')
    if not content:
        return Response({"error": "Message content is required"}, status=400)

    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return Response({
            "error": f"Chat room with ID {room_id} does not exist. Please create a chat room first using /messaging/chat/start/ endpoint."
        }, status=404)

    # Check if user is a participant
    if request.user not in room.participants.all():
        return Response({"error": "You are not a participant in this room"}, status=403)

    message = Message.objects.create(
        room=room,
        sender=request.user,
        content=content
    )

    serializer = MessageSerializer(message)
    return Response(serializer.data, status=201)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_chat_rooms(request):
    """
    List all chat rooms where the current user is a participant
    """
    rooms = ChatRoom.objects.filter(participants=request.user)
    serializer = ChatRoomSerializer(rooms, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_room(request, room_id):
    """
    Get details of a specific chat room
    """
    try:
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        serializer = ChatRoomSerializer(room)
        return Response(serializer.data)
    except ChatRoom.DoesNotExist:
        return Response({"error": f"Chat room with ID {room_id} not found or you are not a participant"}, status=404)


class MessageListCreateView(generics.ListCreateAPIView):
    """
    List all messages in a chat room and create new messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        # Check if room exists and user is a participant
        room = get_object_or_404(ChatRoom, id=room_id, participants=self.request.user)
        return Message.objects.filter(room=room).order_by('timestamp')

    def perform_create(self, serializer):
        room_id = self.kwargs['room_id']
        room = get_object_or_404(ChatRoom, id=room_id, participants=self.request.user)
        serializer.save(sender=self.request.user, room=room)
