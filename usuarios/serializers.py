from rest_framework import serializers
from .models import User, Membership

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'rut',
            'password', 
            'email', 
            'full_name', 
            'phone_number', 
            'address', 
            'is_active', 
            'role',
            'photo'
        ]
        extra_kwargs = {
            'password': {'write_only': True}  # No exponer la contraseña en las respuestas
        }

    # Para manejar el hash de contraseñas al crear o actualizar un usuario
    def create(self, validated_data):
        user = User(
            rut=validated_data['rut'],
            email=validated_data.get('email', ''),  # Usa .get para evitar KeyError
            full_name=validated_data['full_name'],
            phone_number=validated_data.get('phone_number', ''),  # También usar .get aquí
            address=validated_data.get('address', ''),  # Y aquí
            role=validated_data.get('role', None),  # Usa .get para ser seguro
            photo=validated_data.get('photo', None)  # Usa .get para ser seguro
        )
        user.set_password(validated_data['password'])  # Encripta la contraseña
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.role = validated_data.get('role', instance.role)
        instance.photo = validated_data.get('photo', instance.photo)  # Añade manejo para photo

        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)  # Encripta la nueva contraseña si se proporciona

        instance.save()
        return instance

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Incluye los datos del usuario

    class Meta:
        model = Membership
        fields = ['user', 'association', 'start_date', 'end_date', 'status']