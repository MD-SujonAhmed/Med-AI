from django.urls import path, include
from .views import ChatMessageViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'messages', ChatMessageViewSet, basename='chat-messages')


urlpatterns = [
    path('', include(router.urls)),
]