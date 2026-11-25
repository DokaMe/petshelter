from django.db.models import Count, Q
from rest_framework import generics
from people.models import GuardianRegistration
from .models import Animal
from .serializers import CatalogAnimalSerializer


catalog_animals = Animal.objects.select_related('shelter').annotate(
    active_guardian_count=Count(
        'guardians', filter=Q(guardians__status=GuardianRegistration.Status.ACTIVE)
    ),
)


class AnimalListView(generics.ListAPIView):
    queryset = catalog_animals.order_by('-created_at')
    serializer_class = CatalogAnimalSerializer


class AnimalDetailView(generics.RetrieveAPIView):
    queryset = catalog_animals
    serializer_class = CatalogAnimalSerializer
