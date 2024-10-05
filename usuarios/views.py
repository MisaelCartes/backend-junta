from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

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
                house = Housing(address=address,housing_type=housing_type)
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
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'rol':str(usuario.role),
            'rut':str(usuario.rut),
            'email':str(usuario.email),
        }, status=status.HTTP_200_OK)
    
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)