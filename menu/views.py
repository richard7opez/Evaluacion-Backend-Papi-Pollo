from django.shortcuts import render

from .models import Producto
from sucursales.models import Sucursal


def inicio(request):
    contexto = {
        'productos_destacados': Producto.objects.filter(disponible=True).order_by('pk')[:4],
        'sucursales': Sucursal.objects.filter(activa=True).order_by('nombre'),
    }
    return render(request, 'menu/inicio.html', contexto)


def productos(request):
    # Obtener desde la base de datos los productos disponibles
    productos_bd = Producto.objects.filter(disponible=True)

    contexto = {
        'productos': productos_bd,
    }

    return render(request, 'menu/productos.html', contexto)
