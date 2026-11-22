from django.db import models

class Shelter(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Animal(models.Model):

    shelter = models.ForeignKey(
    Shelter,
    on_delete=models.PROTECT,
    related_name='animals',
    null=True,
    blank=True
    )
    
    class Species(models.TextChoices):
        DOG = "dog", "Собака"
        CAT = "cat", "Кошка"
        
    class Status(models.TextChoices):
        AVAILABLE = "available", "Ищет хозяина"
        RESERVED = "reserved", "Зарезервировано"
        ADOPTED = "adopted", "Пристроено"

    name = models.CharField(max_length=100)
    species = models.CharField(
        max_length=20,
        choices=Species.choices
    )
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    gender = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AnimalPhoto(models.Model):
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name="photos"
    )
    image = models.ImageField(upload_to="animals/")
    is_main = models.BooleanField(default=False)
