from rest_framework import serializers
from .models import NeighborAssociation

class NeighborAssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeighborAssociation
        fields = ['id', 'name', 'address', 'contact_email', 'phone_number', 'territory_id']
