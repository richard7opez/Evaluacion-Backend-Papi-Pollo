from django.shortcuts import render
from .models import Sucursal


def inicio_sucursales(request):
    return render(request, 'sucursales/inicio.html')


def listado_sucursales(request):
    sucursales_activas = Sucursal.objects.filter(
        activa=True
    ).order_by('nombre')

    contexto = {
        'sucursales': sucursales_activas
    }

    return render(
        request,
        'sucursales/listado.html',
        contexto
    )