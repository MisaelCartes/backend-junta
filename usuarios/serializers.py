from rest_framework import serializers
from .models import User, Membership

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'rut',
            'password', 
            'email', 
            'first_name', 
            'last_name', 
            'mother_last_name', 
            'phone_number', 
            'address', 
            'is_active', 
            'role',
            'photo'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            rut=validated_data['rut'],
            email=validated_data.get('email', ''),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            mother_last_name=validated_data.get('mother_last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            address=validated_data.get('address', ''),
            role=validated_data.get('role', None),
            photo=validated_data.get('photo', None)
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.mother_last_name = validated_data.get('mother_last_name', instance.mother_last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.role = validated_data.get('role', instance.role)
        instance.photo = validated_data.get('photo', instance.photo)

        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)

        instance.save()
        return instance

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['user', 'association', 'start_date', 'end_date', 'status']
