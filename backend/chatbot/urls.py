from django.urls import path
from .views import ShelterListView, ChatConversationCreateView, ChatMessageCreateView
from .views import (
    ShelterListView,
    ChatConversationCreateView,
    ChatMessageCreateView,
    ChatMessageListView,
    RequestOpenRouter,
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
        ChatMessageCreateView.as_view(),
        name="message-create",
    ),
    path(
    "conversations/<uuid:session_id>/messages/",
    ChatMessageListView.as_view(),
    name="chat-messages"
    ),
    path("abc", RequestOpenRouter.as_view()),
]
