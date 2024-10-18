from django.urls import path
from .views import create_noticia, get_all_noticias,edit_noticia,get_noticia_by_id,delete_noticia

urlpatterns = [
    path('noticias/', get_all_noticias, name='get_all_noticias'),
    path('crear/noticias/', create_noticia, name='create_noticia'),
    path('editar/noticia/', edit_noticia, name='edit_noticia'),
    path('obtener/noticia/', get_noticia_by_id, name='get_noticia_by_id'),
    path('eliminar/noticia/', delete_noticia, name='delete_noticia'),

]