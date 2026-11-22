from django.contrib import admin
from .models import ChatConversation, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "shelter",
        "purpose",
        "species",
        "communication_style",
        "created_at",
    )

    list_filter = ("purpose", "species", "housing")
    inlines = [ChatMessageInline]
