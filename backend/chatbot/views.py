from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from animals.models import Shelter
from animals.serializers import CatalogAnimalSerializer
from animals.views import catalog_animals
from .assistant import AssistantUnavailable, answer
from .models import ChatConversation, ChatMessage
from .serializers import (
    ShelterSerializer,
    ChatConversationSerializer,
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
)

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


class ChatMessageListCreateView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_conversation(self):
        return get_object_or_404(
            ChatConversation,
            session_id=self.kwargs["session_id"],
            user=self.request.user,
        )

    def get_queryset(self):
        return self.get_conversation().messages.all()

    def post(self, request, session_id):
        conversation = self.get_conversation()
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content = serializer.validated_data["content"]

        try:
            reply = answer(conversation, content)
        except AssistantUnavailable:
            return Response(
                {'error': 'ИИ-помощник сейчас недоступен. Попробуйте ещё раз.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        with transaction.atomic():
            user_message = ChatMessage.objects.create(
                conversation=conversation, role=ChatMessage.Role.USER, content=content
            )
            bot_message = ChatMessage.objects.create(
                conversation=conversation, role=ChatMessage.Role.ASSISTANT, content=reply.text
            )
        animals = catalog_animals.in_bulk(reply.animal_ids)
        return Response(
            {
                "user_message": ChatMessageSerializer(user_message).data,
                "bot_message": ChatMessageSerializer(bot_message).data,
                "animals": CatalogAnimalSerializer(
                    [animals[id_] for id_ in reply.animal_ids if id_ in animals],
                    many=True,
                    context={'request': request},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )
