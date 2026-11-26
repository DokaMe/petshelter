from django.contrib import admin
from .models import Animal, Shelter



@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'phone')
    search_fields = ('name', 'city')

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'age', 'status')
    list_filter = ('species', 'status')
    search_fields = ('name', 'breed', 'coat_color')
    readonly_fields = ('detected_coat',)

    @admin.display(description='Окрас по фото')
    def detected_coat(self, animal):
        return animal.photo_coat if animal and animal.photo and animal.coat_photo_name == animal.photo.name else '—'
