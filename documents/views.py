from django.shortcuts import render
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
from .models import CertificateRequest
from usuarios.serializers import UserSerializer
from viviendas.models import Housing, Family, FamilyMember
from usuarios.models import User
# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def get_family_members(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    
    rut = request.query_params.get('rut')
    if not rut:
        return Response({'error': 'RUT is required'}, status=status.HTTP_400_BAD_REQUEST)
    family = Family.objects.filter(user__rut=rut).last()
    family_members = FamilyMember.objects.filter(family=family)
    usuarios_data = []
    if family_members:
        for member in family_members:
                # Crear el diccionario para cada usuario
            usuario_info = {
                "rut": member.rut,
                "firstName": member.first_name,
                "lastName": member.last_name,
                "relationship": member.relationship,
                "family": family.id
            }

            usuarios_data.append(usuario_info)
    # Crear el diccionario para cada usuario
    usuario_info = {
        "rut": family.user.rut,
        "firstName": family.user.first_name,
        "lastName": family.user.last_name,
        "relationship": 'Jefe Hogar',
        "family": family.id
    }

    usuarios_data.append(usuario_info)

    return JsonResponse(usuarios_data, safe=False)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_certificate_request(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    
    rut_user = request.data.get('rutUser')
    rut_user = int(rut_user.replace('.', '').replace('-', ''))

    rut = request.data.get('rutRequest')
    rut = int(rut.replace('.', '').replace('-', ''))

    if not rut:
        return Response({'error': 'RUT request is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not rut_user:
        return Response({'error': 'RUT user is required'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(rut=rut).last()
    family = Family.objects.filter(user__rut=rut_user).last()
    family_member = FamilyMember.objects.filter(family=family,rut=rut).last()

    #VALIDACION SI ES UN CERTIFICADO PARA EL JEFE DE HOGAR
    if not family_member:
        # Crear la solicitud de certificado
        certificate_request = CertificateRequest.objects.create(
            user=user,
        )
        return Response({'message': 'Certificate request created', 'id': certificate_request.id}, status=status.HTTP_201_CREATED)
   
    #VALIDACION SI ES UN CERTIFICADO PARA UN MIEMBRO DE FAMILIA
    if not user:
        # Crear la solicitud de certificado
        certificate_request = CertificateRequest.objects.create(
            family_member=family_member,
        )
        return Response({'message': 'Certificate request created', 'id': certificate_request.id}, status=status.HTTP_201_CREATED)
    #si el rut no corresponde al de un familiar
    if not user and not family_member:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if user and family_member:
        return Response({'error': 'Certificate bad request'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def get_certificate_requests_user(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1,2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    
    rut = request.query_params.get('rut')
    rut = int(rut.replace('.', '').replace('-', ''))
    if not rut:
        return Response({'error': 'RUT is required'}, status=status.HTTP_400_BAD_REQUEST)
    family = Family.objects.filter(user__rut=rut).last()
    family_members = FamilyMember.objects.filter(family=family)
    certificates_family_members = CertificateRequest.objects.filter(family_member__in=family_members)
    certicates_user = CertificateRequest.objects.filter(user=family.user)
    requests_data = []
    if certificates_family_members:
        for certificate in certificates_family_members:
            # Crear el diccionario para cada usuario
            requests = {
                "id":certificate.id,
                "user":certificate.family_member.first_name,
                "rut":certificate.family_member.rut,
                "dateCreation":certificate.creation_date,
                "relationship":certificate.family_member.relationship,
                "status":certificate.get_status_display()
            }
            requests_data.append(requests)

    if certicates_user:
        for certificate in certicates_user:
            # Crear el diccionario para cada usuario
            requests = {
                "id":certificate.id,
                "user":certificate.user.first_name,
                "rut":certificate.user.rut,
                "dateCreation":certificate.creation_date,
                "relationship":'Jefe Hogar',
                "status":certificate.get_status_display()
            }
            requests_data.append(requests)
    if not certicates_user and certificates_family_members:
        return Response({'error': 'Certificates not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return JsonResponse(requests_data, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def get_certificate_requests_admin(request):

    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    
    family_members = FamilyMember.objects.all()
    users = User.objects.all()
    certificates_family_members = CertificateRequest.objects.filter(family_member__in=family_members)
    certicates_user = CertificateRequest.objects.filter(user__in=users)
    requests_data = []
    if certificates_family_members:
        for certificate in certificates_family_members:
            # Crear el diccionario para cada usuario
            requests = {
                "id":certificate.id,
                "user":certificate.family_member.first_name,
                "rut":certificate.family_member.rut,
                "dateCreation":certificate.creation_date,
                "relationship":certificate.family_member.relationship,
                "status":certificate.get_status_display()
            }
            requests_data.append(requests)

    if certicates_user:
        for certificate in certicates_user:
            # Crear el diccionario para cada usuario
            requests = {
                "id":certificate.id,
                "user":certificate.user.first_name,
                "rut":certificate.user.rut,
                "dateCreation":certificate.creation_date,
                "relationship":'Jefe Hogar',
                "status":certificate.get_status_display()
            }
            requests_data.append(requests)
    if not certicates_user and certificates_family_members:
        return Response({'error': 'Certificates not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return JsonResponse(requests_data, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_status_certificate(request):

    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    
    rut_user = request.data.get('rut')
    rut_user = int(rut_user.replace('.', '').replace('-', ''))
    status = request.data.get('status')
    id = request.data.get('id')

    # Validar si el estado es permitido
    if status not in ["APPROVED", "REJECTED"]:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Buscar la solicitud por ID
    try:
        certificate = CertificateRequest.objects.get(id=id).last()
    except CertificateRequest.DoesNotExist:
        return Response({'error': 'Certificate request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Actualizar el estado de la solicitud
    if status == "APPROVED":
        certificate.status = 'approved'
        certificate.rejection_reason = ''  # Limpia cualquier motivo de rechazo previo

    elif status == "REJECTED":
        certificate.status = 'rejected'
        # Agregar el motivo de rechazo si está en los datos
        # rejection_reason = request.data.get('rejection_reason', '')
        # certificate.rejection_reason = rejection_reason

    # Guardar cambios
    certificate.save()

    return Response({'success': 'Status updated successfully'}, status=status.HTTP_200_OK)
