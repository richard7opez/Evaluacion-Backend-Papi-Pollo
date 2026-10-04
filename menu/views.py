from django.shortcuts import render
import json
from pathlib import Path

from .models import Producto


def inicio(request):
    return render(request, 'menu/inicio.html')


def productos(request):
    # Leer el archivo JSON para mantener esta parte del proyecto
    ruta_json = Path(__file__).resolve().parent / 'data' / 'productos.json'

    with open(ruta_json, 'r', encoding='utf-8') as archivo:
        lista_productos = json.load(archivo)

    productos_disponibles_json = []

    for producto in lista_productos:
        if producto['disponible']:
            productos_disponibles_json.append(producto)

    # Obtener desde la base de datos los productos disponibles
    productos_bd = Producto.objects.filter(disponible=True)

    contexto = {
        'productos': productos_bd,
        'productos_json': productos_disponibles_json,
    }

    return render(request, 'menu/productos.html', contexto)