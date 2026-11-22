from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class PersonProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=100, blank=True)

    housing_type = models.CharField(
        max_length=50,
        blank=True
    )

    has_other_animals = models.BooleanField(
        null=True,
        blank=True
    )

    has_children = models.BooleanField(
        null=True,
        blank=True
    )

    experience_with_animals = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class AdoptionApplication(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    person = models.ForeignKey(
        PersonProfile,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.PROTECT,
        related_name="applications"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

class GuardianRegistration(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Активное"
        CANCELLED = "cancelled", "Отменено"

    person = models.ForeignKey(
        PersonProfile,
        on_delete=models.CASCADE,
        related_name="guardianships"
    )

    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.PROTECT,
        related_name="guardians"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "animal"],
                name="unique_person_animal_guardianship"
            )
        ]

    def __str__(self):
        return f"{self.person} — {self.animal}"