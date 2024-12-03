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
from datetime import date
from documents.models import CertificateRequest
from .serializers import UserSerializer
from viviendas.models import Housing, Family, FamilyMember
from django.db.models.functions import TruncMonth
from django.db.models import Count
import re
# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny]) 
def register_user(request):
    if request.method == 'POST':
        data = request.data
        print("Data request", data)

        address = data.get('address', '')

        # Reemplazar "avenida" o "Avenida" por "av." al inicio de la dirección
        if address.lower().startswith("avenida"):
            address = address.replace("Avenida", "av.").replace("avenida", "av.", 1)
        housing_type = data.get('housingType')
        rut = data.get('rut')

        # Limpiar el RUT eliminando puntos y guiones y convertir a int
        rut = rut.replace('.', '').replace('-', '')
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
            'photo': data.get('photo'),
            'date_of_birth':data.get('dateOfBirth'),
            'comuna': data.get('comuna'),
            'region': data.get('region'),
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
                comuna = data.get('comuna', '')
                region = data.get('region', '')

                # Combinar address, comuna y región
                full_address = f"{address}, {comuna}, {region}"
                latitud, longitud = obtener_latitud_longitud(full_address)
                print("LATITUDEEEEE",latitud)
                print("LONGITUFFFFFF",longitud)
                if latitud and longitud:
                    house.latitude = latitud
                    house.longitude = longitud
                    house.save()
            mother_last_name = user.mother_last_name if user and user.mother_last_name else None
            family_name = f"{user.last_name} {mother_last_name}".strip()
            family, _ = Family.objects.get_or_create(housing=house, user=user, defaults={'family_name': family_name})

            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    # Verificar si es inicio de sesión con Google
    is_google_login = request.data.get('isGoogleLogin', False)
    email = request.data.get('email', '').lower()
    rut = request.data.get('rut', '').replace('.', '').replace('-', '').upper()
    password = request.data.get('password', '')

    if is_google_login and email:
        # Autenticar con Google
        try:
            user =User.objects.filter(email=email).last()
            if user and user.is_active:
                # Actualizar la última fecha de inicio de sesión
                user.last_login = datetime.now()
                user.save()

                # Generar los tokens
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                access["rol"] = str(user.role)
                access["rut"] = str(user.rut)
                access["email"] = str(user.email)

                return Response({'token': str(access)}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    elif rut and password:
        # Autenticar con rut y password
        user = authenticate(rut=rut, password=password)
        if user is not None:
            usuario = User.objects.filter(rut=rut).last()
            if usuario and usuario.is_active:
                usuario.last_login = datetime.now()
                usuario.save()

                # Generar los tokens
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                access["rol"] = str(usuario.role)
                access["rut"] = str(usuario.rut)
                access["email"] = str(usuario.email)

                return Response({'token': str(access)}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    return Response({'error': 'Invalid login request'}, status=status.HTTP_400_BAD_REQUEST)

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

    users = User.objects.filter(is_active=True)

    if not users:
        return JsonResponse({'message': 'No users found'}, status=status.HTTP_404_NOT_FOUND)

    usuarios_data = []
    
    for user in users:
        mother_last_name = user.mother_last_name if user and user.mother_last_name else None
        family_name = f"{user.last_name} {mother_last_name}".strip()
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
            "motherLastName": mother_last_name,
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
    rut = rut.replace('.', '').replace('-', '')
    user = User.objects.filter(rut=rut).last()
    miembros_mayoria_edad = False
    # Verificar si el usuario autenticado es admin
    print("rol:", request.user.role) # print temporal
    if request.user.role != 1:  
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    if user and user.is_active:
        user.is_active = False
        user.save()
        family = Family.objects.filter(user=user).last()
        members = FamilyMember.objects.filter(family=family)

        if not members and family:
            family.delete()
        else:
            
            for member in members:
                edad = member.get_age()

                if edad >=18:
                    miembros_mayoria_edad=True
                    family_member = member
                    break
                else:
                    print("Menor de edad")

            if not miembros_mayoria_edad and family and members:
                family.delete()
                members.delete()

        if miembros_mayoria_edad:
            adjusted_data = {
                'rut': family_member.rut,
                'password': family_member.rut[:4],
                'email': family_member.email,
                'first_name': family_member.first_name,
                'last_name': family_member.last_name,
                'mother_last_name':None,
                'phone_number': family_member.phone_number,
                'address': family.housing.address,
                'role': user.role,
                'photo': None
            }
            serializer = UserSerializer(data=adjusted_data)
            
            if serializer.is_valid():
                serializer.save()
                user = User.objects.filter(rut=rut).last()
                family.user = user
                family.save()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)

    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def family_member_delete(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    rut = request.data.get('rut')
    rut_member = request.data.get('rutMember')
    rut = rut.replace('.', '').replace('-', '')
    rut_member = rut_member.replace('.', '').replace('-', '')

    user = User.objects.filter(rut=rut).last()
    if user:
        if user.is_active:
            family = Family.objects.filter(user=user).last()
            if family:
                family_member = FamilyMember.objects.filter(family=family,rut=rut_member).last()
                if family_member:
                    family_member.delete()
                    return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)
                return Response({'error': 'Family member not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': 'Family not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'User not active'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_edit_modal(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    rut = request.data.get('rut')
    rut = rut.replace('.', '').replace('-', '')
    user = User.objects.filter(rut=rut).last()

    if user and user.is_active:
        mother_last_name = user.mother_last_name if user and user.mother_last_name else None
        nombre, apellido, segundo_apellido = user.first_name, user.last_name, mother_last_name
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

    if user and user.is_active:
        mother_last_name = user.mother_last_name if user and user.mother_last_name else None
        actual_name, actual_lastname, actual_mlastname = user.first_name, user.last_name, mother_last_name
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
    # Verificar si el usuario autenticado es admin o user
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    rut = data.get('rut')
    rut_member = data.get('rutMember')

    # Limpiar y convertir el RUT a entero
    rut = rut.replace('.', '').replace('-', '')
    rut_member = rut_member.replace('.', '').replace('-', '')
    user = User.objects.filter(rut=rut).last()

    if user and user.is_active:
        family = Family.objects.filter(user=user).last()
        if family:
            # Comprobar si el miembro de la familia con ese rut ya existe
            family_member = FamilyMember.objects.filter(rut=rut_member).last()
            if family_member:
                return Response({'error': 'Family member with this rut already exists'}, status=status.HTTP_400_BAD_REQUEST)

            # Comprobar si el usuario con ese rut ya existe
            user_member = User.objects.filter(rut=rut_member).last()
            if user_member:
                return Response({'error': 'User with this rut already exists'}, status=status.HTTP_400_BAD_REQUEST)

            # Si pasa ambas verificaciones, proceder a crear el miembro de la familia
            date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
                
            # Crear y guardar el nuevo miembro de la familia
            family_member = FamilyMember(
                family=family,
                first_name=data.get('firstName'),
                last_name=data.get('lastName'),
                rut=rut_member,
                relationship=data.get('relationship'),
                date_of_birth=date_of_birth,
                email=data.get('email', None),
                phone_number=data.get('phoneNumber', None),
                comuna=user.comuna if user and user.comuna else None,
                region=user.region if user and user.region else None
            )
            family_member.save()

            return Response({'message': 'Family member registered successfully'}, status=status.HTTP_200_OK)

        return Response({'error': 'Family not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_rut(request):



    rut = request.query_params.get('rut')
    if not rut:
        return Response({'error': 'RUT is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Limpiar el RUT eliminando puntos y guiones antes de buscar en la base de datos
    cleaned_rut = rut.replace('.', '').replace('-', '')
    
    user = User.objects.filter(rut=cleaned_rut, is_active=True).last()

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_list_map(request):
    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    # Lista para almacenar la información de viviendas y sus familias
    housing_data = []

    # Recorremos cada vivienda en lugar de cada usuario
    housings = Housing.objects.all()
    for housing in housings:
        # Obtener todas las familias asociadas a la vivienda
        families = Family.objects.filter(housing=housing, user__is_active=True)

        # Crear una lista de familias asociadas a esta vivienda
        families_data = []
        for family in families:
            user = family.user  # Obtener el usuario jefe de hogar
            family_members = FamilyMember.objects.filter(family=family)

            # Crear entrada de familia
            family_entry = {
                'user': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'rut': user.rut,
                    'relationship': 'Jefe Hogar',
                    'email': user.email,
                    'phone_number': user.phone_number,
                } if user else None,
                'family_name': family.family_name,
                'family_address': user.address,
                'family_members': [
                    {
                        'first_name': member.first_name,
                        'last_name': member.last_name,
                        'rut': member.rut,
                        'relationship': member.relationship,
                        'email': member.email,
                        'phone_number': member.phone_number,
                    }
                    for member in family_members
                ],
            }

            # Agregar la familia a la lista `families_data` para esta vivienda
            families_data.append(family_entry)

        # Agregar la vivienda junto con sus familias a `housing_data`
        housing_data.append({
            'address': housing.address,
            'latitude': housing.latitude,
            'longitude': housing.longitude,
            'housing_type': housing.housing_type,
            'families': families_data,
        })

    # Respuesta con la estructura solicitada
    response_data = {
        'housing': housing_data,
    }
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_kpis(request):
    today = date.today()
    # Verificar si el usuario autenticado es admin
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    #Iniciacion variables a utilizar
    solicitud_menor = 0
    solicitud_adolescente = 0
    solicitud_adulto = 0
    solicitud_tercera_edad = 0

    # KPI: Cantidad de usuarios registrados
    cantidad_usuarios_registrados = User.objects.filter(is_active=True).count()

    # KPI: Clasificación de solicitudes por tipo de persona
    # Obtener todas las solicitudes
    solicitudes = CertificateRequest.objects.all()
    for solicitud in solicitudes:
        if solicitud.user and solicitud.user.is_active and solicitud.user.date_of_birth:
            birth_date = solicitud.user.date_of_birth
        elif solicitud.family_member and solicitud.family_member.date_of_birth:
            birth_date = solicitud.family_member.date_of_birth
        else:
            continue
        
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        # Clasificar la solicitud según el tipo de persona
        if age <= 13:
            solicitud_menor += 1
        elif 14 <= age <= 18:
            solicitud_adolescente += 1
        elif 19 <= age <= 64:
            solicitud_adulto += 1
        else:
            solicitud_tercera_edad += 1
    cantidad_solicitudes_tipo_persona = {
        'menor': solicitud_menor,
        'adolescente': solicitud_adolescente,
        'adulto': solicitud_adulto,
        'tercera_edad': solicitud_tercera_edad,
    }


    # KPI: Solicitudes mensuales
    solicitudes_mensuales = (
        CertificateRequest.objects
        .annotate(month=TruncMonth('creation_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    cantidad_solicitudes_mensuales = [
        {'month': solicitud['month'].strftime('%Y-%m'), 'count': solicitud['count']}
        for solicitud in solicitudes_mensuales
    ]

    # KPI: Demografía de usuarios y miembros de familia
    demografia = {
        'menor': 0,
        'adolescente': 0,
        'adulto': 0,
        'tercera_edad': 0
    }
    # Obtener usuarios y miembros de familia existentes y calcular sus edades
    personas = list(User.objects.filter(is_active=True)) + list(FamilyMember.objects.all())
    for persona in personas:
        birth_date = persona.date_of_birth
        if birth_date:
            age = today.year - birth_date.year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            if age <= 13:
                demografia['menor'] += 1
            elif 14 <= age <= 18:
                demografia['adolescente'] += 1
            elif 19 <= age <= 64:
                demografia['adulto'] += 1
            else:
                demografia['tercera_edad'] += 1

    response_data = {
        'cantidad_solicitudes_tipo_persona': cantidad_solicitudes_tipo_persona,
        'cantidad_solicitudes_mensuales': cantidad_solicitudes_mensuales,
        'cantidad_usuarios_registrados': cantidad_usuarios_registrados,
        'demografia_usuarios_y_miembros': demografia,
    }
    
    return Response(response_data, status=status.HTTP_200_OK)

# Función para validar el formato y longitud del RUT
def validar_rut(rut):
    # Limpiar el RUT eliminando puntos y guiones
    rut = rut.replace('.', '').replace('-', '')

    # Validar longitud (7 a 9 caracteres)
    if not 7 <= len(rut) <= 9:
        return False

    # Verificar que el dígito verificador sea numérico o una "K" mayúscula
    if not re.match(r'^\d{1,8}[0-9K]$', rut):
        return False

    return True