from pathlib import Path

from django.http import FileResponse, Http404
from django.db import transaction, IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from menu.models import Pedido, Producto
from sucursales.models import Sucursal
from .permissions import PermisosModelo, es_administrador
from .serializers import (
    PedidoAdministradorSerializer, PedidoSerializer,
    ProductoAdministradorSerializer, ProductoSerializer, SucursalSerializer,
    RenovarTokenSerializer,
    ProductoEscrituraSerializer, SucursalEscrituraSerializer, PedidoEscrituraSerializer,
    ErrorSerializer,
    AccessSerializer, TokensSerializer,
)
from .schema import documentar_crud, ERRORES


class SinCacheMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


@extend_schema(tags=["JWT"], description="Credenciales existentes. Devuelve access (5 minutos) y refresh (1 dia).",
               responses={200: TokensSerializer, 400: ErrorSerializer, 401: ErrorSerializer, 429: ErrorSerializer, 500: ErrorSerializer},
               examples=[OpenApiExample("Credenciales ilustrativas", value={"username": "operador", "password": "SU_CONTRASENA"}, request_only=True)])
class ObtenerTokenView(SinCacheMixin, TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "tokens"


@extend_schema(tags=["JWT"], description="Recibe refresh y devuelve access. No renueva la vigencia del refresh.",
               responses={200: AccessSerializer, 400: ErrorSerializer, 401: ErrorSerializer, 429: ErrorSerializer, 500: ErrorSerializer},
               examples=[OpenApiExample("Refresh ilustrativo", value={"refresh": "PEGAR_REFRESH_TOKEN"}, request_only=True)])
class RenovarTokenView(SinCacheMixin, TokenRefreshView):
    serializer_class = RenovarTokenSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "tokens"


class GestionViewSet(SinCacheMixin, viewsets.ModelViewSet):
    permission_classes = [PermisosModelo]
    filter_backends = [filters.SearchFilter]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def create(self, request, *args, **kwargs):
        serializer = self.escritura_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                instancia = serializer.save()
        except IntegrityError:
            raise ValidationError("No se pudo guardar; revisa las relaciones y los datos.")
        return Response(self.get_serializer(instancia).data, status=201)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        try:
            with transaction.atomic():
                instancia = self.get_object()
                # Serializa ediciones concurrentes y mantiene el save() historico de Pedido.
                instancia = type(instancia).objects.select_for_update().get(pk=instancia.pk)
                serializer = self.escritura_class(instancia, data=request.data, partial=parcial,
                                                  context=self.get_serializer_context())
                serializer.is_valid(raise_exception=True)
                instancia = serializer.save()
        except IntegrityError:
            raise ValidationError("No se pudo guardar; revisa las relaciones y los datos.")
        return Response(self.get_serializer(instancia).data)

    def destroy(self, request, *args, **kwargs):
        instancia = self.get_object()
        try:
            with transaction.atomic():
                instancia.delete()
        except ProtectedError:
            raise ValidationError("No se puede eliminar: existen pedidos relacionados.")
        except IntegrityError:
            raise ValidationError("No se puede eliminar un registro relacionado.")
        return Response({"detail": "Registro eliminado."})


@documentar_crud("Productos", ProductoEscrituraSerializer, ProductoSerializer, ProductoAdministradorSerializer,
                 {"nombre": "Producto de demostracion", "precio": 1500, "categoria": "Bebidas", "disponible": True})
class ProductoViewSet(GestionViewSet):
    escritura_class = ProductoEscrituraSerializer
    queryset = Producto.objects.order_by("nombre", "pk")
    serializer_class = ProductoSerializer
    search_fields = ["nombre", "descripcion", "categoria"]

    def get_serializer_class(self):
        if es_administrador(self.request.user):
            return ProductoAdministradorSerializer
        return ProductoSerializer

    @extend_schema(tags=["Productos"], description="Descarga binaria PDF, solo Administrador. No es una respuesta JSON de entidad.",
                   responses={(200, "application/pdf"): OpenApiTypes.BINARY, **ERRORES}, filters=False)
    @action(detail=True, methods=["get"], url_path="ficha")
    def ficha(self, request, pk=None):
        if not es_administrador(request.user):
            raise PermissionDenied("Documento reservado a Administrador en la API.")
        producto = self.get_object()
        if not producto.ficha_tecnica:
            raise Http404("El producto no tiene ficha tecnica.")
        try:
            archivo = producto.ficha_tecnica.open("rb")
        except FileNotFoundError:
            raise Http404("Documento no disponible.")
        response = FileResponse(
            archivo, as_attachment=True,
            filename=Path(producto.ficha_tecnica.name).name,
        )
        response["Cache-Control"] = "private, no-store"
        return response


@documentar_crud("Sucursales", SucursalEscrituraSerializer, SucursalSerializer, ejemplo={
    "nombre": "Sucursal de demostracion", "direccion": "Direccion de prueba", "comuna": "Coquimbo", "activa": True,
})
class SucursalViewSet(GestionViewSet):
    escritura_class = SucursalEscrituraSerializer
    queryset = Sucursal.objects.order_by("nombre", "pk")
    serializer_class = SucursalSerializer
    search_fields = ["nombre", "direccion", "comuna", "telefono"]


@documentar_crud("Pedidos", PedidoEscrituraSerializer, PedidoSerializer, PedidoAdministradorSerializer,
                 {"cliente": "Cliente de prueba", "producto": 1, "sucursal": 1, "cantidad": 2, "estado": "pendiente"})
class PedidoViewSet(GestionViewSet):
    escritura_class = PedidoEscrituraSerializer
    queryset = Pedido.objects.select_related("producto", "sucursal").order_by("-pk")
    serializer_class = PedidoSerializer
    # No buscar campos privados: los resultados podrian revelar coincidencias.
    search_fields = ["producto__nombre", "sucursal__nombre", "estado"]

    def get_serializer_class(self):
        if es_administrador(self.request.user):
            return PedidoAdministradorSerializer
        return PedidoSerializer


@extend_schema(exclude=True)
class RutaNoEncontradaView(SinCacheMixin, APIView):
    def dispatch(self, request, *args, **kwargs):
        # Respuesta JSON incluso para rutas que no corresponden a un recurso.
        from django.http import JsonResponse
        return JsonResponse({"error": {"status": 404, "detail": "Ruta API no encontrada."}}, status=404)
