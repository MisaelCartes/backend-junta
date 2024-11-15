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
from pdfrw import PdfReader, PdfWriter, PdfName, PdfString,IndirectPdfDict
from django.core.files import File
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

import io
import os
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
    if user and not user.is_active:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
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
    if not certicates_user and not certificates_family_members:
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
    if not certicates_user and not certificates_family_members:
        return Response({'error': 'Certificates not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return JsonResponse(requests_data, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_status_certificate(request):

    if request.user.role != 1:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
    
    rut_user = request.data.get('rut')
    rut_user = int(rut_user.replace('.', '').replace('-', ''))
    status_c = request.data.get('status')
    id = request.data.get('id')

    # Validar si el estado es permitido
    if status_c not in ["APPROVED", "REJECTED"]:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Buscar la solicitud por ID
    try:
        certificate = CertificateRequest.objects.filter(id=id).last()
    except CertificateRequest.DoesNotExist:
        return Response({'error': 'Certificate request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Actualizar el estado de la solicitud
    if status_c == "APPROVED":
        certificate.status = 'approved'
        certificate.rejection_reason = ''  # Limpia cualquier motivo de rechazo previo
        certificate.certificate_file = crear_certificado_residencia(certificate)

    elif status_c == "REJECTED":
        certificate.status = 'rejected'
        # Agregar el motivo de rechazo si está en los datos
        # rejection_reason = request.data.get('rejection_reason', '')
        # certificate.rejection_reason = rejection_reason

    # Guardar cambios
    certificate.save()

    return Response({'success': 'Status updated successfully'}, status=status.HTTP_200_OK)

def crear_certificado_residencia(certificate):
    # Definir valores predeterminados
    nombre = "-"
    rut = "-"
    direccion = "-"
    fecha_emision = datetime.now().strftime('%d-%m-%Y')

    # Obtener datos del certificado
    if certificate.user:
        nombre = certificate.user.first_name
        rut = certificate.user.rut
        direccion = certificate.user.address

    if certificate.family_member:
        nombre = certificate.family_member.first_name
        rut = certificate.family_member.rut
        direccion = certificate.family_member.family.housing.address

    # Obtener ciudad y región
    ciudad, region = obtener_ciudad_region(direccion)

    # Crear un buffer en memoria para el archivo PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Encabezado con borde y estilo
    c.setFont("Helvetica-Bold", 20)
    title_y_position = 750
    c.setFillColor(colors.darkblue)
    c.drawCentredString(300, title_y_position, "CERTIFICADO DE RESIDENCIA")
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(2)
    c.line(70, title_y_position - 10, 530, title_y_position - 10)
    
    # Fecha de emisión
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawCentredString(300, title_y_position - 30, f"Fecha de Emisión: {fecha_emision}")

    # Estilos para párrafos de texto justificado
    style = getSampleStyleSheet()['Normal']
    style.fontName = 'Helvetica'
    style.fontSize = 12
    style.leading = 16
    style.alignment = 4  # Justificar el texto

    # Crear texto de párrafos
    texto_1 = f"Por medio del presente documento, la Junta de Vecinos Población Victoria certifica que el Sr./Sra. {nombre}, con cédula de identidad {rut}, reside en la dirección {direccion}, ubicada en la ciudad de {ciudad}, región de {region}, en la República de Chile."
    texto_2 = "Este certificado es emitido a solicitud de la parte interesada para los fines que estime convenientes."
    texto_3 = "La veracidad de esta información es de exclusiva responsabilidad de quien la emite, y el uso indebido de este certificado estará sujeto a las acciones legales pertinentes."

    # Añadir párrafos
    paragraph_y_position = 650
    for texto in [texto_1, texto_2, texto_3]:
        paragraph = Paragraph(texto, style)
        paragraph.wrap(450, 200)  # Definir el ancho del párrafo y espacio de altura
        paragraph.drawOn(c, 70, paragraph_y_position)
        paragraph_y_position -= 50  # Espacio entre párrafos

    # Imagen de firma
    firma_imagen = os.path.join(settings.BASE_DIR, 'documents', 'firmaprueba.jpg')
    if os.path.exists(firma_imagen):
        firma_width = 150
        firma_height = 80
        firma_x_position = 225
        firma_y_position = 270
        c.drawImage(firma_imagen, firma_x_position, firma_y_position, width=firma_width, height=firma_height)

    # Firma de la autoridad con borde
    c.setFont("Helvetica-Bold", 12)
    signature_y_position = 250
    c.setFillColor(colors.black)
    c.drawCentredString(300, signature_y_position, "Autoridad Competente")
    c.setFont("Helvetica", 10)
    c.drawCentredString(300, signature_y_position - 20, "Misael Stalin Cartes Perez, Presidente junta de vecinos.")

    # Guardar el contenido en el buffer en memoria
    c.save()
    buffer.seek(0)

    # Crear un objeto File de Django, simulando un archivo con un nombre
    archivo_pdf = File(buffer, name="certificado_residencia.pdf")

    return archivo_pdf

def obtener_ciudad_region(direccion):
    geolocator = Nominatim(user_agent="mi_aplicacion")
    location = geolocator.geocode(direccion)
    
    if not location:
        return None, None

    ciudad = location.raw.get('address', {}).get('city', None)
    region = location.raw.get('address', {}).get('state', None)

    return ciudad, region

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_certificate(request):
    # Verificar si el usuario autenticado es admin o tiene rol 2
    if request.user.role not in [1, 2]:
        return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

    # Obtener el ID de la solicitud desde los query parameters
    certificate_id = request.query_params.get('id')
    
    # Validar que se proporcionó un ID
    if not certificate_id:
        return Response({'error': 'No certificate ID provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Buscar el certificado por ID
    try:
        certificate = CertificateRequest.objects.get(id=certificate_id)
    except CertificateRequest.DoesNotExist:
        return Response({'error': 'Certificate request not found'}, status=status.HTTP_404_NOT_FOUND)

    # Verificar que el certificado tiene un archivo asociado
    if not certificate.certificate_file:
        return Response({'error': 'Certificate file not found'}, status=status.HTTP_404_NOT_FOUND)

    # Preparar la respuesta con el archivo PDF
    response = HttpResponse(certificate.certificate_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{certificate.certificate_file.name}"'
    
    return response