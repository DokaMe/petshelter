from rest_framework import serializers
from animals.models import Shelter
from .models import ChatConversation


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ['id', 'name', 'city', 'address', 'phone', 'description']


class ChatConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatConversation
        fields = [
            'id',
            'session_id',
            'shelter',
            'purpose',
            'species',
            'housing',
            'communication_style',
            'created_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at']

from .models import ChatMessage


class ChatMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField()


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']