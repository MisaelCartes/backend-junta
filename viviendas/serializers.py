from rest_framework import serializers
from .models import Housing, Family, FamilyMember

class HousingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Housing
        fields = ['id', 'address', 'housing_type']


class FamilySerializer(serializers.ModelSerializer):
    housing = HousingSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user')

    class Meta:
        model = Family
        fields = ['id', 'housing', 'user_id', 'family_name']


class FamilyMemberSerializer(serializers.ModelSerializer):
    family = FamilySerializer(read_only=True)

    class Meta:
        model = FamilyMember
        fields = [
            'id', 'family', 'first_name', 'last_name', 'relationship',
            'date_of_birth', 'email', 'phone_number'
        ]
