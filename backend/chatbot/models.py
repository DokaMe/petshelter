import uuid
from django.db import models
from animals.models import Shelter
from django.conf import settings

class ChatConversation(models.Model):

    class Purpose(models.TextChoices):
        ADOPTION = "adoption", "Забрать домой"
        GUARDIANSHIP = "guardianship", "Опекунство"

    class Species(models.TextChoices):
        CAT = "cat", "Кошка"
        DOG = "dog", "Собака"

    class Housing(models.TextChoices):
        APARTMENT = "apartment", "Квартира"
        HOUSE = "house", "Частный дом"

    class CommunicationStyle(models.TextChoices):
        FRIEND = "friend", "Друг"
        CONSULTANT = "consultant", "Консультант"

    session_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="chat_conversations",
    null=True,
    blank=True
    )

    shelter = models.ForeignKey(
        Shelter,
        on_delete=models.PROTECT,
        related_name="conversations"
    )

    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices
    )

    species = models.CharField(
        max_length=10,
        choices=Species.choices
    )

    housing = models.CharField(
        max_length=20,
        choices=Housing.choices
    )

    communication_style = models.CharField(
        max_length=20,
        choices=CommunicationStyle.choices
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Диалог {self.session_id}"


class ChatMessage(models.Model):

    class Role(models.TextChoices):
        USER = "user", "Пользователь"
        ASSISTANT = "assistant", "ИИ-помощник"

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"
