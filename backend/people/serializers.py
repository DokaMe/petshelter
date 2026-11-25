from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from animals.serializers import AnimalSerializer
from .models import GuardianRegistration
from .models import PersonProfile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=8
    )
    phone = serializers.CharField(
        source='profile.phone',
        max_length=30,
        required=False,
        allow_blank=True
    )
    city = serializers.CharField(
        source='profile.city',
        max_length=100,
        required=False,
        allow_blank=True
    )
    telegram = serializers.CharField(
        source='profile.telegram',
        max_length=100,
        required=False,
        allow_blank=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'phone', 'city', 'telegram']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с такой почтой уже зарегистрирован."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        profile = validated_data.pop('profile', {})
        user = User.objects.create_user(**validated_data)
        PersonProfile.objects.create(user=user, **profile)
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
    telegram = serializers.CharField(source='profile.telegram', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'city', 'telegram']



class GuardianRegistrationSerializer(serializers.ModelSerializer):
    animal = AnimalSerializer(read_only=True)

    class Meta:
        model = GuardianRegistration
        fields = ['id', 'animal', 'status', 'created_at']
