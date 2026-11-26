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
    MAX_ACTIVE_GUARDIANS = 5

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
        ADOPTED = "adopted", "Пристроено"

    name = models.CharField(max_length=100)
    species = models.CharField(
        max_length=20,
        choices=Species.choices
    )
    breed = models.CharField(max_length=100, blank=True)
    age = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    coat_color = models.CharField('Окрас от приюта', max_length=160, blank=True)
    photo_coat = models.CharField(max_length=160, blank=True, editable=False)
    coat_photo_name = models.CharField(max_length=100, blank=True, editable=False)
    gender = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    photo = models.ImageField(
    upload_to="animals/",
    blank=True,
    null=True
    )
    bitrix_source_key = models.CharField(max_length=255, unique=True, null=True, blank=True, editable=False)
    bitrix_photo_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def coat_info(self):
        if self.coat_color.strip():
            return self.coat_color.strip(), 'shelter'
        if self.photo and self.coat_photo_name == self.photo.name and self.photo_coat:
            return self.photo_coat, 'photo'
        return '', None

    def __str__(self):
        return self.name

