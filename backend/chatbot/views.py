from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from animals.models import Shelter
from .models import ChatConversation, ChatMessage
from .serializers import (
    ShelterSerializer,
    ChatConversationSerializer,
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
)

import requests
import json
from config.settings import OPENROUTER_TOKEN
from rest_framework.permissions import IsAuthenticated

class ShelterListView(generics.ListAPIView):
    queryset = Shelter.objects.all()
    serializer_class = ShelterSerializer


class ChatConversationCreateView(generics.CreateAPIView):
    queryset = ChatConversation.objects.all()
    serializer_class = ChatConversationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageCreateView(APIView):

    def post(self, request, session_id):
        conversation = get_object_or_404(
        ChatConversation,
        session_id=session_id,
        user=request.user
        )

        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role=ChatMessage.Role.USER,
            content=serializer.validated_data["content"],
        )

        answer = (
            "Спасибо за сообщение! Расскажите немного больше "
            "о том, какого питомца вы хотели бы найти."
        )

        bot_message = ChatMessage.objects.create(
            conversation=conversation, role=ChatMessage.Role.ASSISTANT, content=answer
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(user_message).data,
                "bot_message": ChatMessageSerializer(bot_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
    permission_classes = [IsAuthenticated]


class ChatMessageListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        conversation = get_object_or_404(
        ChatConversation,
        session_id=session_id,
        user=request.user
        )

        return ChatMessage.objects.filter(conversation=conversation).order_by(
            "created_at"
        )


class RequestOpenRouter(APIView):
    def get(self, request):
        # First API call with reasoning
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_TOKEN}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "model": "deepseek/deepseek-v4.1-flash-1017",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты жесткий эксперт в теме как какать, но ты всегда грубишь. Говори только на русском, если увижу хоть 1 английское слово, то партия тебя переплавит и разрабочткне получит миксу рис и кошка жена",
                        },
                        {"role": "user", "content": "Как какать?"},
                    ],
                    "reasoning": {"enabled": True},
                }
            ),
        )

        # Extract the assistant message with reasoning_details
        response = response.json()
        response = response["choices"][0]["message"]
        print(response)
