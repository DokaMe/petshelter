
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserProfileSerializer
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated


from animals.models import Animal
from .models import PersonProfile, GuardianRegistration
from .serializers import GuardianRegistrationSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

class MyGuardianshipsView(generics.ListAPIView):
    serializer_class = GuardianRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GuardianRegistration.objects.filter(
            person__user=self.request.user,
            status=GuardianRegistration.Status.ACTIVE
        ).select_related('animal').prefetch_related('animal__photos')


class GuardianRegistrationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        animal_id = request.data.get('animal_id')

        if not animal_id:
            return Response(
                {'error': 'Не указан ID животного.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            animal = get_object_or_404(
                Animal.objects.select_for_update(),
                id=animal_id
            )

            active_count = GuardianRegistration.objects.filter(
                animal=animal,
                status=GuardianRegistration.Status.ACTIVE
            ).count()

            person, _ = PersonProfile.objects.get_or_create(
                user=request.user
            )

            registration = GuardianRegistration.objects.filter(
                person=person,
                animal=animal
            ).first()

            if registration and registration.status == GuardianRegistration.Status.ACTIVE:
                return Response(
                    {'error': 'Вы уже оформили опекунство на это животное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if active_count >= 5:
                return Response(
                    {'error': 'У этого животного уже пять активных опекунов.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if registration:
                registration.status = GuardianRegistration.Status.ACTIVE
                registration.save(update_fields=['status'])
            else:
                registration = GuardianRegistration.objects.create(
                    person=person,
                    animal=animal
                )

        return Response(
            GuardianRegistrationSerializer(registration).data,
            status=status.HTTP_201_CREATED
        )