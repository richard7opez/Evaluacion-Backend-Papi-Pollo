from django.urls import path
from . import gestion

urlpatterns = [
    path("productos/<int:pk>/ficha/", gestion.ficha_tecnica, name="producto_ficha"),
    path("<str:entidad>/", gestion.listado, name="gestion_listado"),
    path("<str:entidad>/agregar/", gestion.formulario, name="gestion_agregar"),
    path("<str:entidad>/<int:pk>/", gestion.detalle, name="gestion_detalle"),
    path("<str:entidad>/<int:pk>/editar/", gestion.formulario, name="gestion_editar"),
    path("<str:entidad>/<int:pk>/eliminar/", gestion.eliminar, name="gestion_eliminar"),
]

