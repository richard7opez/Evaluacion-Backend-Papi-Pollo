from django.shortcuts import render
import json
from pathlib import Path


def inicio(request):
    return render(request, 'menu/inicio.html')


def productos(request):
    ruta_json = Path(__file__).resolve().parent / 'data' / 'productos.json'

    with open(ruta_json, 'r', encoding='utf-8') as archivo:
        lista_productos = json.load(archivo)

    productos_disponibles = []

    for producto in lista_productos:
        if producto['disponible']:
            productos_disponibles.append(producto)

    contexto = {
        'productos': productos_disponibles
    }

    return render(request, 'menu/productos.html', contexto)