from drf_spectacular.utils import (
    OpenApiExample, OpenApiResponse, PolymorphicProxySerializer,
    extend_schema, extend_schema_view,
)

from .serializers import ErrorSerializer, MensajeSerializer


ERRORES = {
    codigo: OpenApiResponse(ErrorSerializer, descripcion)
    for codigo, descripcion in (
        (400, "Datos invalidos o relaciones protegidas."),
        (401, "Token ausente, invalido o vencido."),
        (403, "Permisos insuficientes."),
        (404, "Recurso no encontrado."),
        (500, "Error interno sin detalles sensibles."),
    )
}


def documentar_crud(nombre, escritura, lectura, administrador=None, ejemplo=None):
    respuesta = lectura
    if administrador:
        respuesta = PolymorphicProxySerializer(
            component_name=f"{nombre}SegunPerfil",
            serializers=[lectura, administrador], resource_type_field_name=None,
        )
    ejemplos = [OpenApiExample("Entrada ilustrativa", value=ejemplo, request_only=True)]
    salida = OpenApiExample("Respuesta ilustrativa de Administrador", value={"id": 1, **(ejemplo or {})}, response_only=True)
    descripcion = (
        "Permisos reales del modelo Django. Administrador: todas las operaciones; "
        "Operador: consultar, crear y editar; Consulta: solo consultar. "
        "La respuesta depende del perfil. Los campos privados nunca se incluyen para usuarios normales."
    )
    return extend_schema_view(
        list=extend_schema(tags=[nombre], description=descripcion, responses={200: respuesta, **ERRORES}, examples=[salida]),
        retrieve=extend_schema(tags=[nombre], description=descripcion, responses={200: respuesta, **ERRORES}, examples=[salida]),
        create=extend_schema(tags=[nombre], description=descripcion, request=escritura,
                             responses={201: respuesta, **ERRORES}, examples=ejemplos + [salida]),
        update=extend_schema(tags=[nombre], description=descripcion, request=escritura,
                             responses={200: respuesta, **ERRORES}, examples=ejemplos),
        partial_update=extend_schema(tags=[nombre], description=descripcion, request=escritura,
                                     responses={200: respuesta, **ERRORES}, examples=ejemplos),
        destroy=extend_schema(tags=[nombre], description="Solo quien tenga delete_model. "
                              "Producto/Sucursal con pedidos se conservan (400). Pedido permite eliminacion administrativa.",
                              responses={200: MensajeSerializer, **ERRORES},
                              examples=[OpenApiExample("Eliminado", value={"detail": "Registro eliminado."}, response_only=True)]),
    )
