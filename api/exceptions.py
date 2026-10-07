import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler, set_rollback


logger = logging.getLogger(__name__)


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        set_rollback()
        # No registrar cuerpos, cabeceras JWT ni mensajes de excepciones con secretos.
        logger.error("Error API no controlado: %s", type(exc).__name__)
        return Response(
            {"error": {"status": 500, "detail": "Error interno del servidor."}},
            status=500,
        )
    response.data = {"error": {"status": response.status_code, "detail": response.data}}
    return response
