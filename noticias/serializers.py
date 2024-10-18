
from rest_framework import serializers
from .models import Noticia

class NoticiaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()  # Agregar el campo id
    title = serializers.CharField(source='tittle')
    description = serializers.CharField(source='content')
    urlToImage = serializers.ImageField(source='image')
    publishedAt = serializers.DateTimeField(source='date_upload')
    dateVigencia = serializers.DateTimeField(source='date_vigencia')
    source = serializers.CharField()
    category = serializers.CharField()
    author = serializers.CharField()

    class Meta:
        model = Noticia
        fields = ['id','title', 'description', 'urlToImage', 'publishedAt', 'dateVigencia', 'source', 'category', 'author']