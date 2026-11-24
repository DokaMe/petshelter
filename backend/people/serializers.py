from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework import serializers
from animals.serializers import AnimalSerializer
from .models import GuardianRegistration
from .models import PersonProfile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )
    phone = serializers.CharField(
        required=False,
        allow_blank=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с такой почтой уже зарегистрирован."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data.pop('phone', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        PersonProfile.objects.create(
            user=user,
            phone=phone
        )

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        source='profile.phone',
        read_only=True
    )
    city = serializers.CharField(
        source='profile.city',
        read_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'city']



class GuardianRegistrationSerializer(serializers.ModelSerializer):
    animal = AnimalSerializer(read_only=True)

    class Meta:
        model = GuardianRegistration
        fields = ['id', 'animal', 'status', 'created_at']