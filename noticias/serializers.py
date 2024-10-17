
from rest_framework import serializers
from .models import Noticia

class NoticiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Noticia
        fields = ['id', 'tittle', 'content', 'image', 'date_upload','date_vigencia']