from django.urls import path
from .views import (
    start_private_chat, 
    MessageListCreateView, 
    send_message,
    list_chat_rooms,
    get_chat_room
)

urlpatterns = [
    path('chat/start/', start_private_chat, name='start-private-chat'),
    path('chat/rooms/', list_chat_rooms, name='list-chat-rooms'),
    path('chat/<int:room_id>/', get_chat_room, name='get-chat-room'),
    path('chat/<int:room_id>/messages/', MessageListCreateView.as_view(), name='chat-messages'),
    path('chat/<int:room_id>/send/', send_message, name='send-message'),
]
