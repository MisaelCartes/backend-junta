from django.urls import path
from .views import get_family_members,create_certificate_request,get_certificate_requests_user,get_certificate_requests_admin,change_status_certificate,get_certificate
urlpatterns = [
    path('miembros/familia/', get_family_members, name='get_family_members'),
    path('create/solicitud/', create_certificate_request, name='create_certificate_request'),
    path('certificados/list/user/', get_certificate_requests_user, name='get_certificate_requests_user'),
    path('certificados/list/admin/', get_certificate_requests_admin, name='get_certificate_requests_admin'),
    path('certificados/change/status/', change_status_certificate, name='change_status_certificate'),
    path('get/certificate/', get_certificate, name='get_certificate'),
]