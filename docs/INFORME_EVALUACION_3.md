# Informe final local - Evaluacion Sumativa N.º 3

Richard Lopez Nuñez - Programacion Back End - INACAP.
Validacion final: 7 de octubre de 2026.

## Resultado y limites

Implementacion y cierre documental local terminados; suite SQLite aprobada. La web de Evaluacion 2
se conserva. No se ha desplegado esta actualizacion en AWS ni hecho commit/push.
La entrega academica completa requiere actualizar la instancia existente,
demostrar funcionamiento remoto y adjuntar las evidencias reales.

## Validaciones realizadas

| Comprobacion | Resultado exacto / alcance |
|---|---|
| Suite completa | Ran 71 tests in 28.297s; OK |
| Base de la suite | SQLite temporal en memoria, no db.sqlite3 ni MySQL real |
| manage.py check | System check identified no issues (0 silenced). |
| check --deploy local | 5 advertencias: W004, W008, W012, W016, W018; ninguna silenciada |
| Perfil de produccion simulado | Checks de seguridad sin advertencias con variables explicitas, en test aislado |
| makemigrations --check --dry-run | No changes detected |
| showmigrations sobre configuracion MySQL | Todas las migraciones existentes aplicadas [X]; pedidos no tiene migraciones |
| pip check | No broken requirements found. |
| git diff --check | Salida 0, sin errores de whitespace; aviso informativo LF/CRLF en config/tests.py |
| OpenAPI | Esquema validado y generacion fail_on_warn sin advertencias, incluido en la suite |
| JWT | Access, refresh, expiracion, tipo de token, usuario inactivo/eliminado, cambio de contrasena y permisos probados |
| Proteccion de secretos | .env ignorado y no versionado; JWT independiente y sin advertencia de longitud |
| Preservacion SQLite | SHA256 EE4692161FD6166B14449A9FC19C6FD9CE8CBA15BBC8EC3F2DDB690F78394E73, sin cambios |

Comprobacion HTTP local real: /, /productos/, /sucursales/, /api/v1/docs/ y
/api/v1/schema/ responden 200. /api/v1/productos/ sin JWT responde 401.
Swagger fue revisado en navegador: operaciones visibles y Authorize con
esquema jwtAuth (HTTP Bearer). Los flujos autenticados se validaron con usuarios
temporales en los tests, sin cambiar contrasenas ni datos reales.

### MySQL temporal: pendiente por permisos

El intento previo creo un nombre unico para una base separada:
test_papi_api_5880f2b4fda84cc9. El servidor rechazo CREATE DATABASE con error
1044 (Access denied). No se creo esa base ni se ejecuto la suite MySQL.
No se reintento, no se ampliaron permisos, no se modifico ni borro la base real.

Para completar esta validacion hace falta una cuenta de testing con permiso
de crear/eliminar exclusivamente una base temporal aprobada. No utilizar una
base real como TEST.NAME ni otorgar privilegios globales al usuario productivo.
La conectividad/configuracion MySQL y las migraciones SI pudieron consultarse;
esto no equivale a haber aprobado la suite contra MySQL. No se ampliaron
privilegios ni se reintento crear la base en el cierre local.

### Produccion: advertencias locales conocidas

check --deploy informa W004, W008, W012, W016 y W018: HSTS, redireccion
HTTPS, cookies seguras y DEBUG. W009 ya esta resuelta: DJANGO_SECRET_KEY local
y JWT_SIGNING_KEY son fuertes e independientes. No se trasladan secretos de
desarrollo a EC2. No se activa HTTPS local para ocultar advertencias.
Las variables estan preparadas; el dominio/proxy/TLS reales deben verificarse
en EC2. HSTS incluye ahora opciones de subdominios/preload desactivadas por
defecto; activarlas requiere comprobar la politica del dominio. La nueva prueba
de produccion es simulada, no una evidencia de infraestructura.

## Funcionalidad entregada

CRUD REST de Producto, Sucursal y menu.Pedido mediante modelos existentes.
Busquedas y paginacion; FK con PROTECT; precio historico; operaciones atomicas;
validacion de campos, datos y archivos; JSON y errores controlados; JWT y
autorizacion por permisos Django; filtrado de campos privados; Swagger/OpenAPI
con Authorize, ejemplos y esquemas de entrada/salida; documentacion tecnica,
uso real de IA y guia de actualizacion EC2 sin recrear infraestructura.

## Endpoints

Prefijo /api/v1/; origen local habitual http://127.0.0.1:8000.

| Ruta | Metodos |
|---|---|
| productos/ | GET, POST |
| productos/{id}/ | GET, PUT, PATCH, DELETE |
| sucursales/ | GET, POST |
| sucursales/{id}/ | GET, PUT, PATCH, DELETE |
| pedidos/ | GET, POST |
| pedidos/{id}/ | GET, PUT, PATCH, DELETE |
| productos/{id}/ficha/ | GET, PDF protegido |
| token/ | POST, access y refresh |
| token/refresh/ | POST, nuevo access |
| docs/ | GET, Swagger UI |
| schema/ | GET, OpenAPI JSON |

HEAD/OPTIONS auxiliares. DELETE devuelve 200 JSON; POST 201. La descarga PDF
y el HTML de Swagger son excepciones documentadas a las respuestas JSON.

Administrador: CRUD y campos privados de negocio. Operador: lectura, alta y
edicion sin eliminar ni acceder a ficha tecnica API. Consulta: lectura/busqueda.
Sin token: 401; sin permisos: 403. La web conserva sus propios permisos previos.

## Inventario de archivos de Evaluacion 3

Nuevos en api/:
__init__.py, apps.py, permissions.py, serializers.py, views.py, urls.py,
exceptions.py, schema.py, configurar_clave_jwt.py, tests.py, test_escritura.py.

Nuevos en docs/:
API.md, documento_tecnico.md, evidencias_ia.md, ACTUALIZACION_EC2_API.md,
INFORME_EVALUACION_3.md, SEGURIDAD_PRODUCCION.md, EVIDENCIAS_Y_DEFENSA.md.

Modificados existentes:
config/settings.py, config/urls.py, config/tests.py, requirements.txt,
.env.example, .gitignore, README.md.

Archivo privado modificado previamente: .env, para incorporar claves Django
y JWT fuertes. No se incorpora al repositorio y no se cambio en este cierre.
En este cierre se completaron documentacion, configuracion opcional HSTS y
una prueba de produccion. No se rehizo el CRUD ni se modificaron modelos,
migraciones, templates, estilos, contrasenas o permisos web.

El indice mantiene retirados db.sqlite3 y las dos exportaciones sensibles;
siguen intactos localmente. Los secretos actuales no aparecen en los archivos
candidatos examinados. El historial todavia contiene datos sensibles y claves
antiguas: resolverlo separadamente antes de publicar, sin force-push automatico.

Dependencias agregadas: djangorestframework 3.18.3, SimpleJWT 5.5.1, PyJWT 2.15.1,
drf-spectacular 0.30.0 y sidecar 2026.10.1. Django existente se conserva.

## Cumplimiento de la pauta

| Criterio (10 puntos cada uno) | Estado tecnico |
|---|---|
| DRF | CUMPLE localmente |
| Endpoints mantenedores y transaccion | CUMPLE localmente |
| JWT | CUMPLE localmente |
| JSON estructurado | CUMPLE localmente |
| Roles y permisos | CUMPLE localmente |
| Proteccion de informacion sensible | CUMPLE API local; endurecimiento productivo pendiente |
| Swagger/OpenAPI | CUMPLE localmente |
| Recomendaciones de seguridad IA | Aplicadas y documentadas; adjuntar capturas de la conversacion |
| AWS EC2 | PENDIENTE actualizacion y verificacion remota |
| Documentacion y demostracion completa | PARCIAL: documentos listos, evidencia remota/defensa pendientes |

No se asigna una nota ni se afirma que evidencia local sustituye AWS.

## Pasos pendientes para entrega

1. Revision y tratamiento del historial sensible con el propietario; luego
   publicacion Git aprobada, no ejecutada aqui. No hacer push del historial sin revisar.
2. Respaldar la base/media de EC2 y confirmar ruta, rama y servicio existentes.
3. Seguir ACTUALIZACION_EC2_API.md: pull --ff-only, instalar requirements en el
   venv actual, generar JWT_SIGNING_KEY sin mostrarla y revisar variables HTTPS.
4. check, dependencias, migraciones en modo consulta/plan y collectstatic.
   No hay nuevas migraciones API. Revisar cualquier pendiente previa antes de aplicar.
5. Resolver check --deploy, incluyendo SECRET_KEY fuerte, DEBUG=False, TLS y
   cookies seguras, sin copiar secretos de desarrollo.
6. Validar Nginx, reiniciar SOLO el servicio existente y verificar web/API/docs.
7. Suite MySQL solo con cuenta/base de testing autorizadas; sin ellas queda pendiente.
8. Demostrar JWT/Authorize, CRUD por perfiles, archivos y errores en AWS;
   capturas sin tokens ni credenciales; mantener instancia disponible.

Comandos detallados y verificaciones, sin inventar ruta/unidad/dominio remotos:
[ACTUALIZACION_EC2_API.md](ACTUALIZACION_EC2_API.md).

## Documentacion y defensa terminadas localmente

documento_tecnico.md incluye introduccion, descripcion, arquitectura con
diagrama Mermaid, cliente web/API, Django/MySQL y destino EC2, configuracion
DRF, serializers/endpoints, seguridad/JWT/permisos, Swagger, IA, pruebas,
evidencias remotas pendientes, conclusiones y reflexion tecnica.
API.md contiene contrato, ejemplos y demostracion. EVIDENCIAS_Y_DEFENSA.md
enumera 24 evidencias posibles localmente y 12 de AWS, con contenido exacto,
precauciones, guion de 10-15 minutos y preguntas para la defensa.
ACTUALIZACION_EC2_API.md describe la actualizacion de la instancia existente
y todas las variables necesarias, sin inventar dominio, ruta o credenciales.

## UNICO TRABAJO PENDIENTE PARA RICHARD

1. Git/GitHub: decidir y ejecutar el saneamiento del historial sensible y la
   publicacion aprobada; coordinar clones sin operaciones destructivas improvisadas.
2. AWS EC2: respaldo y actualizacion de la instancia existente segun la guia,
   variables reales/TLS, servicios y verificacion remota. Testing MySQL requiere
   una cuenta/base temporal autorizadas; sin ellas se mantiene documentado como no ejecutado.
3. Evidencias reales del despliegue: capturar la demostracion en AWS, sin secretos,
   incorporar las capturas al informe y mantener la instancia disponible.
