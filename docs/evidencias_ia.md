# Apoyo de IA: Evaluacion Sumativa 3

Richard Lopez Nuñez - Programacion Back End - INACAP.

Este registro describe la conversacion real con el asistente Codex/ChatGPT y
las decisiones aplicadas al proyecto. Los prompts se resumen; no se inventan
capturas, ejecuciones en AWS ni consultas a otras herramientas. No existe en
esta sesion evidencia verificable de Gemini: no se le atribuyen resultados.

| Solicitud real resumida | Recomendacion obtenida | Decision y aplicacion | Verificacion |
|---|---|---|---|
| Analizar el proyecto antes de implementar Evaluacion 3 | Reutilizar menu.Pedido y sus FK, aislar /api/v1/ | App api sin modelos; ORM existente | Pruebas de relaciones, historico y ausencia de migraciones |
| Mantener permisos y evitar exponer informacion sensible | Exigir view_model tambien en GET; separar serializers | PermisosModelo, serializers de lectura por perfil y de escritura | 401/403, campos ausentes en GET/POST/PUT/PATCH |
| Corregir la advertencia de firma JWT | Clave aleatoria independiente en entorno, no literal | configurar_clave_jwt y validacion minima en settings | Prueba de clave corta rechazada; suite sin advertencia JWT |
| Implementar CRUD sin romper Evaluacion 2 | Conservar save() y PROTECT, transacciones para escritura | ModelViewSet con captura de relaciones protegidas y bloqueo de edicion | CRUD de tres recursos y regresion web |
| Gestionar archivos de forma segura | Limites, validacion de formato y descarga autorizada | Imagen 5 MB, PDF 10 MB, endpoint ficha protegido | Carga valida, rechazo de falsos/oversize, 401/403/404 |
| Manejar errores sin revelar secretos | Mensajes genericos de servidor, detalles de validacion controlados | api/exceptions.py y error JSON | Test de excepcion inesperada sin texto sensible |
| Documentar y probar desde Swagger | OpenAPI explicito con Bearer, esquemas por perfil y ejemplos | drf-spectacular, sidecar y Authorize | Validacion de esquema; pruebas HTTP y revision local en navegador |
| Preparar AWS sin inventar despliegue | Separar implementacion local de comprobacion remota | Guia de actualizacion de EC2 existente | Comandos preparados; evidencia remota pendiente |

## Evidencia que debe conservar el estudiante

- Exportar o capturar los prompts relevantes de esta conversacion.
- Capturar recomendaciones y explicar cuales se aplicaron y por que.
- Mostrar los archivos y tests correspondientes, no solo la respuesta de la IA.
- Capturar resultado final de check/tests y una ejecucion de Swagger sin tokens.
- Agregar capturas AWS solamente despues de ejecutarlas realmente.

## Fuentes oficiales contrastadas

- https://www.django-rest-framework.org/api-guide/permissions/
- https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html
- https://drf-spectacular.readthedocs.io/en/latest/customization.html

La asistencia de IA no reemplaza la comprension ni la defensa: explicar
autenticacion frente a autorizacion, precio historico, PROTECT y por que
no se retorna el mismo conjunto de campos a todos los usuarios.
