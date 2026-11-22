from django.contrib import admin
from .models import Animal, AnimalPhoto, Shelter


class AnimalPhotoInline(admin.TabularInline):
    model = AnimalPhoto
    extra = 1


@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'phone')
    search_fields = ('name', 'city')

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'age', 'status')
    list_filter = ('species', 'status')
    search_fields = ('name', 'breed')
    inlines = [AnimalPhotoInline]


@admin.register(AnimalPhoto)
class AnimalPhotoAdmin(admin.ModelAdmin):
    list_display = ('animal', 'is_main')