from django.shortcuts import render
import json
from pathlib import Path


def inicio_sucursales(request):
    return render(request, 'sucursales/inicio.html')


def listado_sucursales(request):
    ruta_json = Path(__file__).resolve().parent / 'data' / 'sucursales.json'

    with open(ruta_json, 'r', encoding='utf-8') as archivo:
        lista_sucursales = json.load(archivo)

    sucursales_abiertas = []

    for sucursal in lista_sucursales:
        if sucursal['abierto']:
            sucursales_abiertas.append(sucursal)

    contexto = {
        'sucursales': sucursales_abiertas
    }

    return render(request, 'sucursales/listado.html', contexto)