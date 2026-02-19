from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "updated_at", "created_at")
    search_fields = ("user__username", "title")
    ordering = ("-updated_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "message_type",
        "short_text",
        "created_at",
    )
    list_filter = ("sender", "message_type", "created_at")
    search_fields = ("conversation__user__username", "text_content")
    ordering = ("-created_at",)

    def short_text(self, obj):
        if obj.text_content:
            return obj.text_content[:50]
        return "-"
