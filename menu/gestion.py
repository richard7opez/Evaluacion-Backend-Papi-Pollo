from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from sucursales.forms import SucursalForm
from sucursales.models import Sucursal
from .forms import PedidoForm, ProductoForm
from .models import Pedido, Producto


ENTIDADES = {
    "productos": (Producto, ProductoForm, "Productos", ("nombre", "descripcion", "categoria")),
    "sucursales": (Sucursal, SucursalForm, "Sucursales", ("nombre", "direccion", "comuna", "telefono")),
    "pedidos": (Pedido, PedidoForm, "Pedidos", ("cliente", "producto__nombre", "sucursal__nombre")),
}


def configuracion(request, entidad, accion="view"):
    if entidad not in ENTIDADES:
        raise Http404
    model, form, titulo, campos = ENTIDADES[entidad]
    opts = model._meta
    permiso = f"{opts.app_label}.{accion}_{opts.model_name}"
    if not request.user.has_perm(permiso):
        raise PermissionDenied
    return model, form, titulo, campos


def contexto_permisos(request, model):
    opts = model._meta
    return {
        f"puede_{accion}": request.user.has_perm(f"{opts.app_label}.{accion}_{opts.model_name}")
        for accion in ("add", "change", "delete")
    }


@login_required
@require_safe
def listado(request, entidad):
    model, _, titulo, campos = configuracion(request, entidad)
    registros = model.objects.all()
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    if entidad == "pedidos":
        registros = registros.select_related("producto", "sucursal")
        opciones = list(Pedido.Estado.choices)
        if estado in Pedido.Estado.values:
            registros = registros.filter(estado=estado)
    else:
        campo_estado = "disponible" if entidad == "productos" else "activa"
        opciones = [("1", "Activos"), ("0", "Inactivos")]
        if estado in ("0", "1"):
            registros = registros.filter(**{campo_estado: estado == "1"})
    if q:
        consulta = Q()
        for campo in campos:
            consulta |= Q(**{f"{campo}__icontains": q})
        if entidad == "pedidos" and q.isdecimal() and len(q) < 19:
            consulta |= Q(pk=int(q))
        registros = registros.filter(consulta)
    pagina = Paginator(registros, 10).get_page(request.GET.get("page"))
    return render(request, "gestion/listado.html", {
        "entidad": entidad, "titulo": titulo, "pagina": pagina,
        "q": q, "estado": estado, "opciones_estado": opciones,
        **contexto_permisos(request, model),
    })


@login_required
@require_safe
def detalle(request, entidad, pk):
    model, _, titulo, _ = configuracion(request, entidad)
    registros = model.objects.all()
    if entidad == "pedidos":
        registros = registros.select_related("producto", "sucursal")
    return render(request, "gestion/detalle.html", {
        "entidad": entidad, "titulo": titulo,
        "registro": get_object_or_404(registros, pk=pk),
        **contexto_permisos(request, model),
    })


@login_required
@require_http_methods(["GET", "POST"])
def formulario(request, entidad, pk=None):
    model, form_class, titulo, _ = configuracion(request, entidad, "change" if pk else "add")
    configuracion(request, entidad, "view")
    registro = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST if request.method == "POST" else None,
                      request.FILES if request.method == "POST" else None, instance=registro)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Registro actualizado." if pk else "Registro creado.")
            return redirect("gestion_listado", entidad=entidad)
        messages.error(request, "Revisa los campos indicados.")
    return render(request, "gestion/formulario.html", {
        "form": form, "entidad": entidad, "titulo": titulo, "registro": registro,
    })


@login_required
@require_http_methods(["GET", "POST"])
def eliminar(request, entidad, pk):
    model, _, titulo, _ = configuracion(request, entidad, "delete")
    configuracion(request, entidad, "view")
    registro = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        try:
            registro.delete()
        except ProtectedError:
            messages.error(request, "No se puede eliminar: hay pedidos asociados a este registro.")
        else:
            messages.success(request, "Registro eliminado.")
        return redirect("gestion_listado", entidad=entidad)
    return render(request, "gestion/eliminar.html", {
        "entidad": entidad, "titulo": titulo, "registro": registro,
    })


@login_required
@require_safe
def ficha_tecnica(request, pk):
    configuracion(request, "productos")
    producto = get_object_or_404(Producto, pk=pk)
    if not producto.ficha_tecnica:
        raise Http404
    try:
        archivo = producto.ficha_tecnica.open("rb")
    except FileNotFoundError:
        raise Http404("Documento no disponible.")
    return FileResponse(archivo, as_attachment=True,
                        filename=Path(producto.ficha_tecnica.name).name)


@login_required
@require_safe
def documento_media(request, nombre):
    configuracion(request, "productos")
    producto = get_object_or_404(Producto, ficha_tecnica=f"documentos/productos/{nombre}")
    return ficha_tecnica(request, producto.pk)

