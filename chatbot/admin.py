from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'sender', 'message_type', 'text_content', 'created_at']
    list_filter = ['sender', 'message_type', 'created_at']
    search_fields = ['user__username', 'text_content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'