
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from rest_framework import status
from .models import Noticia
from .serializers import NoticiaSerializer
# Create your views here.


@api_view(['POST'])
def create_noticia(request):
    # Validar que se envió el campo 'tittle'
    tittle = request.data.get('tittle')
    content = request.data.get('content')
    image = request.FILES.get('image')
    date_vigencia = request.data.get('date_vigencia')

    # Validación del título
    if not tittle:
        return Response({'error': 'El campo "tittle" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(tittle) > 200:
        return Response({'error': 'El campo "tittle" no puede tener más de 200 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación del contenido
    if not content:
        return Response({'error': 'El campo "content" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación de la imagen
    if image:
        if not image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            return Response({'error': 'Solo se permiten imágenes en formato .jpg, .jpeg o .png.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación de la fecha de vigencia
    if date_vigencia:
        try:
            # Intenta convertir la fecha de vigencia al formato deseado
            date_vigencia_formatted = datetime.strptime(date_vigencia, '%Y-%m-%d %H:%M')
            
            # Asegúrate de que la fecha de vigencia sea una fecha futura
            if date_vigencia_formatted < datetime.now():
                return Response({"error": "La fecha de vigencia debe ser una fecha futura."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Formato de fecha de vigencia no válido. Usa 'AAAA-MM-DD HH:MM'."}, status=status.HTTP_400_BAD_REQUEST)

    # Si las validaciones son correctas, utilizar el serializador
    serializer = NoticiaSerializer(data=request.data)
    if serializer.is_valid():
        # Guardar la fecha de vigencia en el serializador (asegúrate de que el modelo tenga este campo)
        serializer.validated_data['date_vigencia'] = date_vigencia_formatted
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Si el serializador encuentra errores
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_noticias(request):
    # Obtener solo las noticias que están vigentes
    now = datetime.now()
    noticias_vigentes = Noticia.objects.filter(date_vigencia__gte=now)  # Filtrar por fecha de vigencia
    serializer = NoticiaSerializer(noticias_vigentes, many=True)  # Serializar el queryset
    return Response(serializer.data, status=status.HTTP_200_OK)

