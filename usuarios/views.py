from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from django.contrib.auth.decorators import login_required
from .models import User
from .serializers import UserSerializer
from viviendas.models import Housing, Family, FamilyMember

# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny]) 
def register_user(request):
    if request.method == 'POST':
        data = request.data
        print("Data request", data)

        address = data.get('address')
        housing_type = data.get('housingType')
        rut = data.get('rut')

        # Limpiar el RUT eliminando puntos y guiones y convertir a int
        rut = int(rut.replace('.', '').replace('-', ''))
        print("Rut: ", rut)

        # Inicializar role: por defecto 2 (MEMBER)
        role = 2  # Default to MEMBER

        # Verificar si se especifica el rol como ADMIN (ignorar mayúsculas/minúsculas)
        if data.get('role', '').lower() == "admin":
            role = 1  # Cambiar a ADMIN si se especifica

        adjusted_data = {
            'rut': rut,
            'password': data.get('password'),
            'email': data.get('email'),
            'first_name': data.get('firstName'),
            'last_name': data.get('lastName'),
            'mother_last_name': data.get('motherLastName'),
            'phone_number': data.get('phoneNumber'),
            'address': address,
            'role': role,
            'photo': data.get('photo')
        }

        serializer = UserSerializer(data=adjusted_data)

        if serializer.is_valid():
            serializer.save()
            user = User.objects.filter(rut=rut).last()

            # Se obtiene vivienda
            house, _ = Housing.objects.get_or_create(
                address=address,
                defaults={'housing_type': housing_type, 'latitude': None, 'longitude': None}
            )

            # Obtener latitud y longitud si no existe
            if house.latitude is None or house.longitude is None:
                latitud, longitud = obtener_latitud_longitud(address)
                if latitud and longitud:
                    house.latitude = latitud
                    house.longitude = longitud
                    house.save()

            family_name = f"{user.last_name} {user.mother_last_name}".strip()
            family, _ = Family.objects.get_or_create(housing=house, user=user, defaults={'family_name': family_name})

            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny]) 
def login_user(request):
    rut = request.data.get('rut')
    password = request.data.get('password')

    user = authenticate(rut=rut, password=password)
    if user is not None:
        usuario = User.objects.filter(rut=rut).last()
        usuario.last_login = datetime.now()
        usuario.save()

        # Generar el RefreshToken y AccessToken
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token  # No convertir a str

        # Agregar datos adicionales al token de acceso
        access["rol"] = str(usuario.role)
        access["rut"] = str(usuario.rut)
        access["email"] = str(usuario.email)

        return Response({'token': str(access)}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

def obtener_latitud_longitud(direccion):
    geolocator = Nominatim(user_agent="mi_aplicacion")
    try:
        ubicacion = geolocator.geocode(direccion)
        if ubicacion:
            return ubicacion.latitude, ubicacion.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return obtener_latitud_longitud(direccion)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_datatable(request):
    
    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.all()

    if not users:
        return JsonResponse({'message': 'No users found'}, status=status.HTTP_404_NOT_FOUND)

    usuarios_data = []
    
    for user in users:
        family_name = f"{user.last_name} {user.mother_last_name}".strip()
        house, _ = Housing.objects.get_or_create(
            address=user.address,
            defaults={'housing_type': 'Casa', 'latitude': None, 'longitude': None}
        )

        # Obtener latitud y longitud si no existen
        if house.latitude is None or house.longitude is None:
            latitud, longitud = obtener_latitud_longitud(user.address)
            if latitud and longitud:
                house.latitude = latitud
                house.longitude = longitud
                house.save()

        Family.objects.get_or_create(housing=house, user=user, defaults={'family_name': family_name})

        # Crear el diccionario para cada usuario
        usuario_info = {
            "firstName": user.first_name,
            "rut": user.rut,
            "lastName": user.last_name,
            "motherLastName": user.mother_last_name,
            "address": user.address,
            "phoneNumber": user.phone_number,
            "email": user.email,
            "password": "",  
            "role": user.role  
        }

        usuarios_data.append(usuario_info)

    return JsonResponse(usuarios_data, safe=False)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete(request):

    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    rut = request.data.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    user = User.objects.filter(rut=rut).last()

    # Verificar si el usuario autenticado es admin
    print("rol:", request.user.role) # print temporal
    if request.user.role != 1:  
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    if user:
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)

    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_edit_modal(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    rut = request.data.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    user = User.objects.filter(rut=rut).last()

    if user:
        nombre, apellido, segundo_apellido = user.first_name, user.last_name, user.mother_last_name
        email = user.email or ''
        phone_number = user.phone_number or ''
        
        return JsonResponse({
            'firstName': nombre,
            'lastName': apellido,
            'motherLastName': segundo_apellido,
            'email': email,
            'phoneNumber': phone_number
        })

    return JsonResponse({'message': 'No user found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_edit(request):

   # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    rut = request.data.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    data = request.data
    user = User.objects.filter(rut=rut).last()

    if user:
        actual_name, actual_lastname, actual_mlastname = user.first_name, user.last_name, user.mother_last_name
        name = data.get('firstName') or actual_name
        lastname = data.get('lastName') or actual_lastname
        mlastname = data.get('motherLastName') or actual_mlastname
        email = data.get('email') or user.email
        phone_number = data.get('phoneNumber') or user.phone_number

        user.email = email
        user.first_name = name
        user.last_name = lastname
        user.mother_last_name = mlastname
        user.phone_number = phone_number
        user.save()

        return Response({'message': 'User edited successfully'}, status=status.HTTP_200_OK)

    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def family_member_register(request):

    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    rut = data.get('rut')
    rut_member = data.get('rutMember')

    # Limpiar y convertir el RUT a entero
    rut = int(rut.replace('.', '').replace('-', ''))
    rut_member = int(rut_member.replace('.', '').replace('-', ''))
    user = User.objects.filter(rut=rut).last()

    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:  
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    if user:
        family = Family.objects.filter(user=user).last()
        if family:
            # Comprobar si el miembro de la familia ya está registrado
            family_member = FamilyMember.objects.filter(rut=rut_member).last()
            if not family_member:
                date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
                
                family_member = FamilyMember(
                    family=family,
                    first_name=data.get('firstName'),
                    last_name=data.get('lastName'),
                    rut=rut_member,
                    relationship=data.get('relationship'),
                    date_of_birth=date_of_birth,
                    email=data.get('email', None),
                    phone_number=data.get('phoneNumber', None)
                )
                family_member.save()

                return Response({'message': 'Family member registered successfully'}, status=status.HTTP_200_OK)

            return Response({'error': 'Family member already registered'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': 'Family not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_rut(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    rut = request.query_params.get('rut')
    if not rut:
        return Response({'error': 'RUT is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Limpiar el RUT eliminando puntos y guiones antes de buscar en la base de datos
    cleaned_rut = rut.replace('.', '').replace('-', '')
    
    user = User.objects.filter(rut=cleaned_rut).last()

    if not user:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user)
    user_data = serializer.data

    formatted_data = {
        "firstName": user_data.get('first_name', ""),
        "rut": user_data.get('rut', ""),
        "lastName": user_data.get('last_name', ""),
        "motherLastName": user_data.get('mother_last_name', ""),
        "address": user_data.get('address', ""),
        "phoneNumber": user_data.get('phone_number', ""),
        "email": user_data.get('email', ""),
        "password": "",  # No devolvemos la contraseña por motivos de seguridad
        "role": user_data.get('role', 2)  # Default a MEMBER si no hay rol definido
    }

    return Response(formatted_data, status=status.HTTP_200_OK)
