from django.urls import path
from .views import (
    ChatAPIView, 
    ChatHistoryAPIView, 
    ConversationDetailAPIView,
    ClearChatHistoryAPIView,
    DeleteConversationAPIView
)

app_name = 'chatbot'

urlpatterns = [
    # Chat endpoint
    path('chat/', ChatAPIView.as_view(), name='chat'),
    
    # History endpoints
    path('history/', ChatHistoryAPIView.as_view(), name='chat_history'),  # List all conversations
    path('history/<int:conversation_id>/', ConversationDetailAPIView.as_view(), name='conversation_detail'),  # Get specific conversation messages
    
    # Deletion endpoints
    path('history/clear/', ClearChatHistoryAPIView.as_view(), name='clear_history'),  # Delete all conversations
    path('history/<int:conversation_id>/delete/', DeleteConversationAPIView.as_view(), name='delete_conversation'),  # Delete specific conversation
]