from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_sucursales, name='inicio_sucursales'),
    path('listado/', views.listado_sucursales, name='listado_sucursales'),
]