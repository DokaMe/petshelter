from django.conf import settings
from rest_framework import serializers
from animals.models import Shelter
from .models import ChatConversation, ChatMessage


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ['id', 'name', 'city', 'address', 'phone', 'description']


class QuestionnaireSerializer(serializers.Serializer):
    gender = serializers.ChoiceField(choices=['male', 'female', 'any'])
    has_children = serializers.BooleanField()
    has_other_animals = serializers.BooleanField()
    had_animals_before = serializers.BooleanField(allow_null=True)
    activity = serializers.ChoiceField(choices=['active', 'calm'])


class ChatConversationSerializer(serializers.ModelSerializer):
    questionnaire = QuestionnaireSerializer(required=False, allow_null=True)
    assistant_enabled = serializers.SerializerMethodField()

    def get_assistant_enabled(self, conversation):
        return bool(settings.OPENROUTER_TOKEN)

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
            'questionnaire',
            'assistant_enabled',
            'created_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at']

class ChatMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']
