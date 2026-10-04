from django.contrib import admin
from .models import Producto


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