from django.contrib import admin
from .models import Producto, Pedido


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "categoria",
        "precio",
        "disponible",
        "fecha_creacion",
    )

    search_fields = (
        "nombre",
        "categoria",
        "descripcion",
    )

    list_filter = (
        "categoria",
        "disponible",
    )

    ordering = (
        "nombre",
    )


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "producto", "sucursal", "cantidad", "precio_unitario", "total", "estado")
    search_fields = ("cliente", "producto__nombre", "sucursal__nombre")
    list_filter = ("estado", "sucursal")
    list_select_related = ("producto", "sucursal")
    readonly_fields = ("precio_unitario", "total", "fecha_creacion", "fecha_actualizacion")
