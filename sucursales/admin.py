from django.contrib import admin
from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "direccion",
        "comuna",
        "telefono",
        "horario",
        "activa",
        "fecha_creacion",
    )

    search_fields = (
        "nombre",
        "direccion",
        "comuna",
        "telefono",
    )

    list_filter = (
        "comuna",
        "activa",
    )

    ordering = (
        "nombre",
    )

    readonly_fields = (
        "fecha_creacion",
        "fecha_actualizacion",
    )