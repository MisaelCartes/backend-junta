from django.shortcuts import render

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime

from .models import User
from .serializers import UserSerializer
from viviendas.models import Housing


# Create your views here.
@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        data = request.data
        print("Data request", data)

        # Crear un full_name concatenando los nombres
        full_name = f"{data.get('firstName', '')} {data.get('lastName', '')} {data.get('motherLastName', '')}"
        address = data.get('address')
        housing_type =data.get('housingType')
        rut = data.get('rut')
        
        # Limpiar el RUT eliminando puntos y comas y convertir a int
        rut = int(rut.replace('.', '').replace('-', ''))
        print("RUTTTTT", rut)

        # Inicializar role
        role = None
        if data.get('role') == "MEMBER":
            role = 2

        adjusted_data = {
            'rut': rut,
            'password': data.get('password'),
            'email': data.get('email'),
            'full_name': full_name,
            'phone_number': data.get('phoneNumber'),
            'address': address,
            'role': role,
            'photo': data.get('photo')
        }

        serializer = UserSerializer(data=adjusted_data)

        if serializer.is_valid():
            serializer.save()

            # Se obtiene vivienda
            house = Housing.objects.filter(address=address).last()
            # Si no existe en el sistema se crea
            if not house:
                latitud, longitud = obtener_latitud_longitud(address)
                if latitud and longitud:
                    print("latitud",latitud)
                    print("longitud",longitud)
                house = Housing(address=address,housing_type=housing_type,latitude=latitud,longitude=longitud)
                house.save()

            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    # Obtiene las credenciales del cuerpo de la solicitud
    rut = request.data.get('rut')
    password = request.data.get('password')

    # Autentica al usuario
    user = authenticate(rut=rut, password=password)
    if user is not None:

        # Si la autenticación es exitosa, genera el token
        usuario = User.objects.filter(rut=rut).last()
        
        # Actualiza el campo last_login del usuario con datetime
        usuario.last_login = datetime.now()
        usuario.save()
        print(usuario.last_login)
        token = RefreshToken.for_user(user)
        # Agrega los datos adicionales al access token
        token["rol"] = str(usuario.role)
        token["rut"] = str(usuario.rut)
        token["email"] = str(usuario.email)
        print(token)
        return Response({
            'token': str(token),
        }, status=status.HTTP_200_OK)
    
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

def obtener_latitud_longitud(direccion):
    geolocator = Nominatim(user_agent="mi_aplicacion")
    try:
        ubicacion = geolocator.geocode(direccion)
        if ubicacion:
            latitud = ubicacion.latitude
            longitud = ubicacion.longitude
            return latitud, longitud
        else:
            return None, None
    except GeocoderTimedOut:
        return obtener_latitud_longitud(direccion)


@api_view(['POST'])
def users_datatable(request):
    usuarios = User.objects.all().values('full_name', 'rut', 'email', 'phone_number', 'address', 'role')
    
    if not usuarios.exists():
        return JsonResponse({'message': 'No users found'}, status=status.HTTP_404_NOT_FOUND)  # Puedes usar otro código de estado si lo prefieres
    
    return JsonResponse(list(usuarios), safe=False)


@api_view(['POST'])
def user_delete(request):
    rut = request.data.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    user = User.objects.filter(rut=rut).last()
    if user:
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def user_edit_modal(request):
    rut = request.data.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    user = User.objects.filter(rut=rut).last()
    if user:
        #NOMBRE Y APELLIDOS
        # Asumimos que tienes un campo `full_name` en el modelo que contiene el nombre completo.
        nombre, apellido, segundo_apellido = user.full_name_conv()

        #CORREO
        email = user.email if user.email else ''

        #NUMERO TELEFONICO
        phone_number = user.phone_number if user.phone_number else ''
        
        return JsonResponse({
            'firstName': nombre,
            'lastName': apellido,
            'motherLastName': segundo_apellido,
            'email':email,
            'phoneNumber':phone_number
        })
    else:
        return JsonResponse({'message': 'No user found'}, status=status.HTTP_404_NOT_FOUND)  # Puedes usar otro código de estado si lo prefieres
    

@api_view(['POST'])
def user_edit(request):
    rut = request.data.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    data = request.data
    user = User.objects.filter(rut=rut).last()
    if user:
        #se obtienen datos actuales en caso de que los datos de entrada vengan vacios 
        actual_name, actual_lastname, actual_mlastname = user.full_name_conv()

        name = data.get('firstName') if data.get('firstName') else actual_name
        lastname = data.get('lastName') if data.get('lastName') else actual_lastname
        mlastname = data.get('motherLastName') if data.get('motherLastName') else actual_mlastname
        full_name = f"{name} {lastname} {mlastname}"
        email = data.get('email') if data.get('email') else user.email
        phone_number = data.get('phoneNumber') if data.get('phoneNumber') else user.phone_number

        user.email = email
        user.full_name =full_name
        user.phone_number = phone_number
        user.save()

        return Response({'message': 'User edited successfully'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
