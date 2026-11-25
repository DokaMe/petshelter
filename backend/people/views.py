
from django.db import connection, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from animals.models import Animal
from .models import PersonProfile, GuardianRegistration
from .serializers import GuardianRegistrationSerializer, RegisterSerializer, UserProfileSerializer

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
        ).select_related('animal__shelter').order_by('-created_at', '-pk')


class GuardianRegistrationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            animal_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1).run_validation(
                request.data.get('animal_id')
            )
        except serializers.ValidationError:
            return Response(
                {'error': 'Укажите ID животного.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            if connection.vendor == 'sqlite':
                # SQLite ignores select_for_update. Take its write lock before reading the slot count.
                Animal.objects.filter(pk=animal_id).update(status=F('status'))
            animal = get_object_or_404(
                Animal.objects.select_for_update(),
                id=animal_id
            )
            if animal.status != Animal.Status.AVAILABLE:
                return Response(
                    {'error': 'Этот питомец уже дома. Оформление опеки недоступно.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            registration = GuardianRegistration.objects.filter(
                person__user=request.user,
                animal=animal
            ).first()

            if registration and registration.status == GuardianRegistration.Status.ACTIVE:
                return Response(
                    {'error': 'Вы уже оформили опекунство на это животное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            active_count = animal.guardians.filter(status=GuardianRegistration.Status.ACTIVE).count()
            if active_count >= Animal.MAX_ACTIVE_GUARDIANS:
                return Response(
                    {'error': 'У этого животного уже пять активных опекунов.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if registration:
                registration.status = GuardianRegistration.Status.ACTIVE
                registration.save(update_fields=['status'])
            else:
                person, _ = PersonProfile.objects.get_or_create(user=request.user)
                registration = GuardianRegistration.objects.create(
                    person=person,
                    animal=animal
                )

        return Response(
            GuardianRegistrationSerializer(registration, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
