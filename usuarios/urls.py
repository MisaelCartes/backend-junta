from django.urls import path
from .views import register_user, login_user, users_datatable,user_delete,user_edit,user_edit_modal,family_member_register, get_user_by_rut

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
    path('users/list/', users_datatable, name='users_datatable'),
    path('user/edit/', user_edit, name='user_edit'),
    path('user/edit/modal', user_edit_modal, name='user_edit_modal'),
    path('user/delete/', user_delete, name='user_delete'),
    path('register/family/member/', family_member_register, name='family_member_register'),
    path('user/list/one/', get_user_by_rut, name='get_user_by_rut'),
]