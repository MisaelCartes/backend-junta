from django.urls import path
from .views import create_noticia, get_all_noticias

urlpatterns = [
    path('noticias/', get_all_noticias, name='get_all_noticias'),
    path('crear/noticias/', create_noticia, name='create_noticia'),
]