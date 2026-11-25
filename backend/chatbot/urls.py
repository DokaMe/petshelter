from django.urls import path
from .views import (
    ShelterListView,
    ChatConversationCreateView,
    ChatMessageListCreateView,
)

urlpatterns = [
    path("shelters/", ShelterListView.as_view(), name="shelter-list"),
    path(
        "conversations/",
        ChatConversationCreateView.as_view(),
        name="conversation-create",
    ),
    path(
        "conversations/<uuid:session_id>/messages/",
        ChatMessageListCreateView.as_view(),
        name="message-create",
    ),
]
