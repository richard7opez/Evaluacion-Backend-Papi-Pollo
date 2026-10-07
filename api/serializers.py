from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema_field
from rest_framework.reverse import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from menu.models import Pedido, Producto
from sucursales.models import Sucursal
from .permissions import es_administrador


class RenovarTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # Comprobar tambien usuario eliminado/inactivo y cambio de contrasena.
        JWTAuthentication().get_user(self.token_class(attrs["refresh"]))
        return super().validate(attrs)


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = (
            "id", "nombre", "descripcion", "precio", "categoria", "disponible",
            "imagen", "fecha_creacion", "fecha_actualizacion",
        )
        read_only_fields = fields


class ProductoAdministradorSerializer(ProductoSerializer):
    ficha_tecnica = serializers.SerializerMethodField()

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_ficha_tecnica(self, producto):
        if not producto.ficha_tecnica:
            return None
        return reverse(
            "api:producto-ficha", args=[producto.pk], request=self.context.get("request")
        )

    class Meta(ProductoSerializer.Meta):
        fields = ProductoSerializer.Meta.fields + ("ficha_tecnica",)
        read_only_fields = fields


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = (
            "id", "nombre", "direccion", "comuna", "telefono", "horario", "activa",
            "fecha_creacion", "fecha_actualizacion",
        )
        read_only_fields = fields


class PedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)

    class Meta:
        model = Pedido
        fields = (
            "id", "producto", "producto_nombre", "sucursal", "sucursal_nombre",
            "cantidad", "estado", "fecha_creacion", "fecha_actualizacion",
        )
        read_only_fields = fields


class PedidoAdministradorSerializer(PedidoSerializer):
    total = serializers.IntegerField(read_only=True)

    class Meta(PedidoSerializer.Meta):
        fields = PedidoSerializer.Meta.fields + (
            "cliente", "observaciones", "precio_unitario", "total",
        )
        read_only_fields = fields


class EscrituraSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            desconocidos = set(data.keys()) - set(self.fields)
            if desconocidos:
                raise serializers.ValidationError({"detail": "El cuerpo contiene campos no autorizados."})
        return super().to_internal_value(data)


class ProductoEscrituraSerializer(EscrituraSerializer):
    imagen = serializers.ImageField(required=False, allow_null=True)
    ficha_tecnica = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Producto
        fields = ("nombre", "descripcion", "precio", "categoria", "disponible", "imagen", "ficha_tecnica")

    def to_internal_value(self, data):
        if hasattr(data, "keys") and "ficha_tecnica" in data and not es_administrador(self.context["request"].user):
            raise PermissionDenied("Solo Administrador puede cambiar la ficha tecnica desde la API.")
        return super().to_internal_value(data)

    def validate_imagen(self, imagen):
        if imagen and imagen.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("La imagen no puede superar 5 MB.")
        return imagen

    def validate_ficha_tecnica(self, archivo):
        if not es_administrador(self.context["request"].user):
            raise PermissionDenied("Solo Administrador puede cambiar la ficha tecnica desde la API.")
        if archivo:
            if archivo.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("El documento no puede superar 10 MB.")
            firma = archivo.read(5)
            archivo.seek(0)
            if not archivo.name.lower().endswith(".pdf") or firma != b"%PDF-":
                raise serializers.ValidationError("Adjunta una ficha tecnica en formato PDF.")
        return archivo


class SucursalEscrituraSerializer(EscrituraSerializer):
    class Meta:
        model = Sucursal
        fields = ("nombre", "direccion", "comuna", "telefono", "horario", "activa")


class PedidoEscrituraSerializer(EscrituraSerializer):
    cantidad = serializers.IntegerField(min_value=1, max_value=10000, default=1)

    class Meta:
        model = Pedido
        fields = ("cliente", "producto", "sucursal", "cantidad", "estado", "observaciones")
        extra_kwargs = {
            "cliente": {"write_only": True},
            "observaciones": {"write_only": True},
        }


class MensajeSerializer(serializers.Serializer):
    detail = serializers.CharField()


class DetalleErrorSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    detail = serializers.JSONField()


class ErrorSerializer(serializers.Serializer):
    error = DetalleErrorSerializer()


class AccessSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)


class TokensSerializer(AccessSerializer):
    refresh = serializers.CharField(read_only=True)
