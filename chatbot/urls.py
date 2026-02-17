from django.urls import path
from .views import ChatAPIView, ChatHistoryAPIView, ClearChatHistoryAPIView

app_name = 'chatbot'

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('history/', ChatHistoryAPIView.as_view(), name='chat_history'),
    path('history/clear/', ClearChatHistoryAPIView.as_view(), name='clear_history'),
]