from rest_framework import serializers
from .models import Animal, AnimalPhoto


class AnimalPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalPhoto
        fields = ['id', 'image', 'is_main']


class AnimalSerializer(serializers.ModelSerializer):
    photos = AnimalPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Animal
        fields = [
            'id',
            'name',
            'species',
            'breed',
            'age',
            'description',
            'gender',
            'status',
            'created_at',
            'photos'
        ]