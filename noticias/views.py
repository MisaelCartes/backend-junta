
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
# from django.contrib.auth.decorators import login_required
from datetime import datetime
from rest_framework import status
from .models import Noticia
from .serializers import NoticiaSerializer
# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_noticia(request):

   # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    # Obtener los datos del request
    tittle = request.data.get('title')
    content = request.data.get('description')
    image = request.FILES.get('urlToImage')
    date_upload = request.data.get('publishedAt')
    date_vigencia = request.data.get('dateVigencia')
    source = request.data.get('source')
    category = request.data.get('category')
    author = request.data.get('author')

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
            # Convertir la fecha de vigencia al formato deseado
            date_vigencia_formatted = datetime.strptime(date_vigencia, '%Y-%m-%d %H:%M')
            if date_vigencia_formatted < datetime.now():
                return Response({"error": "La fecha de vigencia debe ser una fecha futura."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Formato de fecha de vigencia no válido. Usa 'AAAA-MM-DD HH:MM'."}, status=status.HTTP_400_BAD_REQUEST)

    # Validación del source
    if not source:
        return Response({'error': 'El campo "source" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(source) > 100:
        return Response({'error': 'El campo "source" no puede tener más de 100 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación de la fecha de publicación (date_upload)
    if date_upload:
        try:
            # Convertir la fecha de subida al formato deseado
            date_upload_formatted = datetime.strptime(date_upload, '%Y-%m-%d %H:%M')
        except ValueError:
            return Response({"error": "Formato de fecha de subida no válido. Usa 'AAAA-MM-DD HH:MM'."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        date_upload_formatted = datetime.now()  # Si no se proporciona, usar la fecha y hora actual

    # Validación de la categoría
    if not category:
        return Response({'error': 'El campo "category" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(category) > 50:
        return Response({'error': 'El campo "category" no puede tener más de 50 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación del autor
    if not author:
        return Response({'error': 'El campo "author" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(author) > 100:
        return Response({'error': 'El campo "author" no puede tener más de 100 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    # Crear la noticia directamente en el modelo
    try:
        noticia = Noticia.objects.create(
            tittle=tittle,
            content=content,
            image=image,
            date_vigencia=date_vigencia_formatted,
            source=source,
            date_upload=date_upload_formatted,
            category=category,
            author=author
        )
        return Response({"success": "Noticia creada exitosamente", "noticia_id": noticia.id}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_all_noticias(request):
    # Obtener solo las noticias que están vigentes
    now = datetime.now()
    noticias_vigentes = Noticia.objects.filter(date_vigencia__gte=now)  # Filtrar por fecha de vigencia
    serializer = NoticiaSerializer(noticias_vigentes, many=True)  # Serializar el queryset
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_noticia(request):

    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    # Obtener el ID de la noticia desde el cuerpo de la solicitud
    noticia_id = request.data.get('id')
    
    if not noticia_id:
        return Response({'error': 'El campo "id" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Buscar la noticia por su ID
        noticia = Noticia.objects.get(id=noticia_id)
    except Noticia.DoesNotExist:
        return Response({'error': 'Noticia no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    # Obtener los datos del request
    tittle = request.data.get('title')
    content = request.data.get('description')
    image = request.FILES.get('urlToImage')
    date_upload = request.data.get('publishedAt')
    date_vigencia = request.data.get('dateVigencia')
    source = request.data.get('source')
    category = request.data.get('category')
    author = request.data.get('author')

    # Validación del título
    if not tittle:
        return Response({'error': 'El campo "title" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(tittle) > 200:
        return Response({'error': 'El campo "title" no puede tener más de 200 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación del contenido
    if not content:
        return Response({'error': 'El campo "description" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación de la imagen (opcional)
    if image:
        if not image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            return Response({'error': 'Solo se permiten imágenes en formato .jpg, .jpeg o .png.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación de la fecha de publicación (opcional)
    if date_upload:
        try:
            # Validar y convertir la fecha de publicación al formato correcto
            date_upload = datetime.strptime(date_upload, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return Response({'error': 'El campo "publishedAt" tiene un formato incorrecto. Usa "AAAA-MM-DDTHH:MM:SS".'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación de la fecha de vigencia
    if date_vigencia:
        try:
            # Validar y convertir la fecha de vigencia al formato correcto
            date_vigencia = datetime.strptime(date_vigencia, '%Y-%m-%dT%H:%M:%S')
            # Validar que la fecha de vigencia sea futura
            if date_vigencia < datetime.now():
                return Response({"error": "La fecha de vigencia debe ser una fecha futura."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'El campo "dateVigencia" tiene un formato incorrecto. Usa "AAAA-MM-DDTHH:MM:SS".'}, status=status.HTTP_400_BAD_REQUEST)

    # Validar el campo fuente
    if not source:
        return Response({'error': 'El campo "source" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validar la categoría
    if not category:
        return Response({'error': 'El campo "category" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validar el autor
    if not author:
        return Response({'error': 'El campo "author" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    # Actualizar los campos de la noticia
    noticia.tittle = tittle
    noticia.content = content
    if image:  # Si se ha subido una nueva imagen
        noticia.image = image
    if date_upload:  # Actualizar la fecha de publicación si se proporciona
        noticia.date_upload = date_upload
    noticia.date_vigencia = date_vigencia
    noticia.source = source
    noticia.category = category
    noticia.author = author

    # Guardar la noticia actualizada
    noticia.save()

    return Response({'message': 'Noticia actualizada correctamente.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_noticia_by_id(request):

    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    noticia_id = request.query_params.get('id')
    # Buscar la noticia por ID
    noticia = Noticia.objects.filter(id=noticia_id).last()
    if noticia:
        # Serializar la noticia
        serializer = NoticiaSerializer(noticia)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Noticia no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_noticia(request):

    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    noticia_id = request.data.get('id')
    # Buscar la noticia por ID
    noticia = Noticia.objects.filter(id=noticia_id).last()

    if noticia:
        noticia.delete()
        return Response({'message': 'Noticia eliminada correctamente.'}, status=status.HTTP_200_OK)
    return Response({'error': 'Noticia not found'}, status=status.HTTP_404_NOT_FOUND)
 