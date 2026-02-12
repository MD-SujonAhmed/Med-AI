import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsNormalUser
from .models import ChatMessage
from .serializers import ChatMessageSerializer


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        content = request.data.get("content")
        if not content:
            return Response({"detail": "content is required for text-only mode."}, status=400)

        # 1) Save user message
        user_msg = ChatMessage.objects.create(
            user=request.user,
            content=content,
        )

        # 2) Call FastAPI /ai/chat
        ai_base = getattr(settings, "AI_BASE_URL", "http://localhost:8001")
        url = f"{ai_base.rstrip('/')}/ai/chat"

        try:
            r = requests.post(url, json={"text": content}, timeout=60)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            # Save assistant error message
            ChatMessage.objects.create(
                user=request.user,
                content=f"AI service error: {str(e)}",
            )
            return Response(
                {
                    "detail": "AI service call failed.",
                    "error": str(e),
                    "user_message": ChatMessageSerializer(user_msg).data,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 3) Extract assistant reply (fallback keys)
        assistant_text = (
            data.get("text")
            or data.get("message")
            or data.get("reply")
            or data.get("assistant")
            or str(data)
        )

        # 4) Save assistant message
        assistant_msg = ChatMessage.objects.create(
            user=request.user,
            content=assistant_text,
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
                "ai_raw": data,
            },
            status=status.HTTP_201_CREATED,
        )