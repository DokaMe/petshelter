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
    search_fields = ('name', 'breed')
