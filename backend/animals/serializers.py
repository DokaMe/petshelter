from rest_framework import serializers
from .models import Animal

class AnimalSerializer(serializers.ModelSerializer):
    shelter_name = serializers.CharField(source='shelter.name', read_only=True, allow_null=True)

    class Meta:
        model = Animal
        fields = [
            'id',
            'name',
            'shelter',
            'shelter_name',
            'species',
            'breed',
            'age',
            'description',
            'gender',
            'status',
            'photo',
            'created_at'
        ]


class CatalogAnimalSerializer(AnimalSerializer):
    guardianship_slots = serializers.SerializerMethodField()

    class Meta(AnimalSerializer.Meta):
        fields = [*AnimalSerializer.Meta.fields, 'guardianship_slots']

    def get_guardianship_slots(self, animal):
        return max(0, Animal.MAX_ACTIVE_GUARDIANS - animal.active_guardian_count)
