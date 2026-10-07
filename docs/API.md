# Papi Pollo: API de Evaluacion Sumativa 3

Autor: Richard Lopez Nuñez. Programacion Back End, INACAP.

## Contrato

Base local con runserver: http://127.0.0.1:8000/api/v1/.
Mantener la barra final. En AWS usar el dominio HTTPS existente, no localhost.

| URL relativa | Metodos | Resultado |
|---|---|---|
| productos/ | GET, POST | Lista paginada / alta |
| productos/{id}/ | GET, PUT, PATCH, DELETE | Consulta / reemplazo / edicion parcial / baja |
| sucursales/ | GET, POST | Lista paginada / alta |
| sucursales/{id}/ | GET, PUT, PATCH, DELETE | Consulta / reemplazo / edicion parcial / baja |
| pedidos/ | GET, POST | Lista paginada / alta |
| pedidos/{id}/ | GET, PUT, PATCH, DELETE | Consulta / reemplazo / edicion parcial / baja |
| productos/{id}/ficha/ | GET | PDF privado de Administrador |
| token/ | POST | Access y Refresh |
| token/refresh/ | POST | Access nuevo |
| schema/ | GET | OpenAPI JSON |
| docs/ | GET | Swagger UI |

HEAD y OPTIONS se admiten como metodos auxiliares. Los recursos requieren
Authorization: Bearer ACCESS_TOKEN. Token, Swagger y esquema son publicos;
no contienen registros reales. La sesion web no sustituye el token API.

GET listados acepta `?search=texto&page=1`. Tamano de pagina: 20.
Busqueda: nombre/descripcion/categoria en Producto; nombre/direccion/comuna/
telefono comercial en Sucursal; producto/sucursal/estado en Pedido. No se busca
por cliente ni observaciones para evitar deducir datos privados por coincidencias.

```json
{"count": 1, "next": null, "previous": null, "results": [{"id": 1, "nombre": "Ejemplo"}]}
```

El ejemplo anterior muestra el envoltorio; los campos completos estan en OpenAPI.
GET detalle devuelve un objeto, no una lista. POST devuelve 201 y el objeto
filtrado segun perfil. PUT/PATCH devuelven 200. DELETE devuelve 200:

```json
{"detail": "Registro eliminado."}
```

## Perfiles y campos

| Perfil existente | GET/busqueda | POST | PUT/PATCH | DELETE | Ficha PDF API |
|---|---|---|---|---|---|
| Administrador | Si | Si | Si | Si | Si |
| Operador | Si | Si | Si | No | No |
| Consulta | Si | No | No | No | No |
| Sin permisos | No | No | No | No | No |

Se verifican permisos Django por modelo, no solo el nombre del perfil. Los
permisos se consultan en cada peticion: quitar permisos invalida el acceso
aunque el token no haya vencido. Superusuario tiene las facultades de Django.
No se modifican los permisos de las vistas web ya existentes.

Producto: nombre, descripcion, precio de venta publico, categoria, disponibilidad,
imagen y fechas son operacionales. Ficha tecnica: solo Administrador en API.
Sucursal: direccion, comuna, horario y telefono del negocio son informacion
comercial publica; no almacenar telefonos personales en este campo.
Pedido: id, FK, nombres de producto/sucursal, cantidad, estado y fechas son
operacionales. Cliente, observaciones, precio_unitario y total se reservan al
Administrador en las respuestas. El Operador puede aportar cliente/observaciones
para registrar la operacion, pero no recuperarlos mediante la API. En PATCH
puede omitirlos; PUT requiere los campos obligatorios del contrato.
No hay endpoint de usuarios, contrasenas, correos privados o credenciales.
No se implementa propiedad individual de pedidos: el modelo no tiene usuario FK.

## Ejemplos de cuerpos de entrada

Todos los valores siguientes son ilustrativos, no datos ni precios reales.
Los ids deben corresponder a registros existentes en el entorno de demostracion.

Producto:
```json
{"nombre": "Producto de prueba", "descripcion": "Demostracion", "precio": 1500, "categoria": "Bebidas", "disponible": true}
```
Sucursal:
```json
{"nombre": "Sucursal de prueba", "direccion": "Direccion de prueba", "comuna": "Coquimbo", "telefono": "", "horario": "", "activa": true}
```
Pedido:
```json
{"cliente": "Cliente de prueba", "producto": 1, "sucursal": 1, "cantidad": 2, "estado": "pendiente", "observaciones": "Demostracion"}
```
PATCH Pedido:
```json
{"cantidad": 3, "estado": "preparacion"}
```

Precio unitario, total, ids y fechas no se aceptan como campos de escritura.
Cantidad: 1 a 10000. Estados: pendiente, preparacion, entregado, cancelado.
Precio de venta: entero no negativo, como en el modelo existente. FK inexistentes
son 400. Pedido.save() toma el precio al registrar/cambiar producto y conserva
el historico en las demas ediciones. Administrador puede eliminar pedidos;
Producto y Sucursal referenciados no se eliminan (PROTECT, respuesta 400).

## Archivos

Usar multipart/form-data para imagen y ficha_tecnica de Producto. No enviar
Content-Type con boundary escrito manualmente: el cliente lo genera.
Imagen: formato validado por Pillow/DRF, maximo 5 MB. Documento: extension PDF,
firma %PDF- y maximo 10 MB. Esta validacion no sustituye analisis antivirus
ni certifica la inocuidad de un PDF. La descarga usa attachment, autenticacion
y Cache-Control privado; no expone la ruta fisica de almacenamiento.
El PDF es una respuesta binaria application/pdf, excepcion documentada al JSON,
al igual que el HTML de Swagger. Omitir archivos en PATCH conserva los existentes.
Enviar null elimina la referencia cuando el perfil tiene autorizacion; no borra
el archivo antiguo del almacenamiento. No hay limpieza automatica de media.

## JWT y Swagger paso a paso

1. Abrir /api/v1/docs/ y expandir POST token/. Pulsar Try it out.
2. Ingresar las credenciales del usuario existente y Execute. No capturar ni
   compartir la respuesta que muestra access/refresh.
3. Pulsar Authorize y pegar SOLO el valor access, sin anteponer Bearer.
4. Apply credentials, Close; ejecutar GET y observar 200.
5. Con Consulta probar POST: 403. Sin Authorize, GET debe devolver 401.
6. Probar CRUD con registros exclusivamente de demostracion y rol autorizado.
7. POST token/refresh/ con {"refresh": "VALOR_PRIVADO"} devuelve access nuevo.
8. Actualizar Authorize con el nuevo access. El refresh no sirve como access.

Access dura 5 minutos; refresh 1 dia. La renovacion no prolonga el refresh.
Usuario desactivado/eliminado o cambio de contrasena impiden acceso/renovacion.
JWT no crea sesiones web ni actualiza last_login. Logout web no revoca tokens;
el consumidor debe descartarlos y no persistirlos en capturas/logs. No hay blacklist
ni nuevas tablas. Swagger no conserva autorizacion entre recargas.
Token endpoints: 10 peticiones/minuto por IP con cache local. Es mitigacion basica,
no defensa completa ante fuerza bruta distribuida; en AWS complementar en proxy
o cache compartida. Nunca enviar credenciales/tokens por HTTP fuera de localhost.

## Errores

```json
{"error": {"status": 400, "detail": {"cantidad": ["Dato invalido."]}}}
```

200 consulta/edicion/baja; 201 alta; 400 validacion/relacion protegida; 401 token;
403 permiso; 404 inexistente; 405 metodo no soportado; 415 formato no admitido;
429 limite de intentos; 500 mensaje generico sin trazas ni credenciales.
detail puede ser texto, objeto o lista segun el error. No enviar secretos en URL.

## Verificacion sin datos reales

PowerShell, desde el proyecto, en una terminal dedicada a pruebas:
```powershell
$env:DB_ENGINE = 'sqlite'
.\venv\Scripts\python.exe -B manage.py test --noinput
Remove-Item Env:DB_ENGINE
.\venv\Scripts\python.exe -B manage.py check
.\venv\Scripts\python.exe -B manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe -B -m pip check
git diff --check
```
La suite crea una base SQLite en memoria y media temporales; no usa db.sqlite3.
El cambio DB_ENGINE solo afecta esa terminal; no edita .env. Para validar MySQL
usar una cuenta/base de testing separadas. No ejecutar flush, loaddata ni tests
con TEST.NAME apuntando a una base real.

Defensa: mostrar CRUD por rol, precio historico, bloqueo PROTECT, archivos y
JSON de error; Swagger Authorize y refresh; esquema; pruebas; finalmente la
misma demostracion en AWS HTTPS. Las capturas deben ocultar credenciales/tokens.
