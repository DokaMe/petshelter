from rest_framework import generics
from .models import Animal
from .serializers import AnimalSerializer


class AnimalListView(generics.ListAPIView):
    queryset = Animal.objects.all().order_by('-created_at')
    serializer_class = AnimalSerializer


class AnimalDetailView(generics.RetrieveAPIView):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer