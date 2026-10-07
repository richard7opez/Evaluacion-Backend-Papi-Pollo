# Evidencias y defensa - Papi Pollo, Evaluacion Sumativa 3

Richard Lopez Nuñez - Programacion Back End - INACAP.

Esta es una lista de capturas por obtener, no una afirmacion de que existen.
Las pruebas automatizadas son evidencia tecnica adicional, no sustituyen las
capturas que solicite el profesor. No mostrar .env, passwords, Authorization,
cookies, tokens ni respuestas completas de token. Usar datos ficticios y una
base de demostracion separada para acciones destructivas. Nunca borrar registros
originales para preparar evidencias. Conservar originales de capturas sin editar
en un lugar privado; entregar solo versiones sin secretos.

## A. Capturas posibles localmente

1. **Web anterior:** Inicio, Menu y Sucursales reconocibles; URL local visible,
   productos e informacion existentes. Puede ser un conjunto de tres capturas.
2. **Login y navegacion por perfiles:** sesion iniciada con cada perfil y menus
   correspondientes; no mostrar entrada de password ni datos privados reales.
3. **Estructura DRF:** api/ y config/urls.py mostrando /api/v1/; modelos existentes
   en menu/sucursales. No abrir .env en el editor ni en pestañas visibles.
4. **Relaciones:** menu.Pedido con FK Producto/Sucursal, PROTECT y precio historico;
   no mostrar un segundo Pedido ni afirmar que existe una tabla nueva.
5. **Swagger general:** titulo Papi Pollo API, recursos Productos/Sucursales/Pedidos,
   operaciones GET/POST/PUT/PATCH/DELETE y boton Authorize.
6. **Esquema OpenAPI:** /api/v1/schema/, version, paths y esquema jwtAuth Bearer.
7. **Obtencion de JWT:** endpoint token, codigo 200 y nombres access/refresh;
   ocultar los valores y el password, incluidas secciones curl/request/response.
8. **Authorize:** dialogo jwtAuth HTTP Bearer y estado autorizado. Ocultar token.
9. **GET autorizado:** lista JSON paginada y detalle con 200; datos de demostracion.
10. **Busqueda y paginacion:** parametros search/page y respuesta count/results,
    siguiente pagina cuando existan mas de 20 registros de prueba.
11. **POST de los tres recursos:** una captura por recurso con cuerpo ficticio,
    codigo 201 y el id creado. No incluir datos de clientes reales.
12. **PUT y PATCH:** una captura de cada metodo, 200 y cambio comprobado por GET.
13. **DELETE permitido:** Administrador eliminando SOLO un registro de prueba,
    200 JSON y posterior GET 404. Repetir para las tres entidades si se exige.
14. **Integridad de Pedido:** respuesta con FK, total de prueba y precio historico
    conservado tras cambiar precio de catalogo. Administrador, datos ficticios.
15. **PROTECT:** intento de borrar mantenedor de prueba referenciado; 400 y
    posterior GET 200 demostrando que se conservo.
16. **401 y 403:** GET sin token 401; DELETE de Operador 403; POST de Consulta 403.
    Ocultar Authorization en la captura y no usar cuentas reales sin permiso.
17. **Filtrado:** misma entidad ficticia consultada con Administrador y Consulta;
    cliente/observaciones/precio_unitario/total ausentes para Consulta.
18. **Archivos:** carga multipart valida, imagen visible, ficha descargada con
    Administrador, rechazo 403 a perfil no autorizado y 400 a archivo invalido.
19. **Refresh y vencimiento:** renovacion 200 y acceso con token nuevo; token
    vencido/invalido 401. Ocultar ambos valores y cualquier curl generado.
20. **Errores y validaciones:** 400 por cantidad/FK/estado invalido y 404 inexistente.
    El 500 seguro se demuestra con el test, no provocando un fallo en la base real.
21. **Pruebas y checks:** total de tests y OK, check sin issues, No changes detected,
    pip check correcto y validacion OpenAPI. Mostrar el backend temporal de tests.
22. **Variables seguras:** .env.example con valores vacios, settings leyendo entorno
    y salida de git check-ignore .env; JAMAS mostrar .env real. Las cinco advertencias
    locales HTTPS/DEBUG deben explicarse, no ocultarse.
23. **IA:** solicitud real, recomendacion, decision aplicada y test relacionado.
    Usar evidencias_ia.md como indice, no inventar conversaciones con otras IA.
24. **Arquitectura:** diagrama del documento tecnico y explicacion de ambas rutas:
    web con sesion/CSRF y API con JWT/permisos, compartiendo ORM y MySQL.

## B. Capturas obligatorias posteriores en AWS

1. **Instancia existente activa:** estado running y nombre identificable de Papi
   Pollo; ocultar identificadores de cuenta innecesarios. No crear otra instancia.
2. **IP publica o DNS:** direccion utilizada, junto con la URL real de la aplicacion.
3. **Acceso remoto:** terminal SSH ya conectada, hostname y carpeta real del
   proyecto; no mostrar clave privada, archivos pem ni cadenas de conexion secretas.
4. **Entorno operativo:** venv existente, version Python, dependencias y check.
5. **Base y migraciones:** motor MySQL/MariaDB activo y showmigrations aplicado;
   sin contrasenas, hashes, tablas auth/session ni registros de clientes reales.
6. **Servicios:** Gunicorn existente activo, nginx -t correcto y servicio Nginx.
7. **Web desplegada:** Inicio, Menu, Sucursales y login sobre el dominio/IP real,
   preservando la interfaz de Evaluacion 2.
8. **Swagger remoto:** barra de URL HTTPS visible, recursos/methods y Authorize;
   esquema OpenAPI accesible desde ese mismo origen.
9. **JWT remoto:** token/refresh exitosos y consulta autorizada, con valores de
   tokens/password completamente ocultos. Evidencia de 401 y 403 tambien.
10. **CRUD remoto:** POST/GET/PUT/PATCH/DELETE con registros exclusivamente de
    demostracion, codigos HTTP y FK visibles. PROTECT y precio historico.
11. **Archivos y perfiles remotos:** imagen/PDF autorizado; rechazo de acceso
    indebido, y campos sensibles filtrados al comparar perfiles de prueba.
12. **Seguridad y conectividad:** HTTPS valido, check --deploy despues de la
    configuracion real y respuesta desde un navegador externo. La instancia
    debe mantenerse disponible durante la evaluacion, no solo para la captura.

## Guion de defensa (10 a 15 minutos)

1. **Contexto (1 min):** la web administra el negocio; la API permite integracion
   de clientes externos. Se extendio Evaluacion 2, no se reconstruyo.
2. **Arquitectura (1 min):** explicar el diagrama, rutas web/API, ORM y MySQL;
   Nginx/Gunicorn en EC2 frente a runserver local.
3. **Contrato (2 min):** Swagger, recursos, parametros, entrada y respuestas;
   access/refresh y Authorize sin exponer valores al publico.
4. **Transaccion (3 min):** crear datos ficticios, registrar Pedido con FK,
   editarlo, observar precio historico y bloqueo PROTECT. DELETE solo sobre
   datos nuevos de demostracion, despues de eliminar su Pedido de prueba.
5. **Seguridad (2 min):** Consulta no escribe, Operador no elimina, Administrador
   administra; 401 vs 403 y diferencias de campos de respuesta.
6. **Archivos/errores (1 min):** carga/descarga autorizada y validacion 400/404.
7. **Calidad (1 min):** tests en base temporal, check, migraciones, uso documentado
   de IA; no afirmar que SQLite tests equivalen a MySQL tests.
8. **AWS y cierre (2 min):** URL real, servicios y evidencias. Explicar limitaciones
   honestamente si falta una verificacion remota; no presentar comandos como pruebas.

## Preguntas previsibles

**Autenticacion vs autorizacion:** JWT identifica; permisos Django deciden cada
operacion. Tener token valido no concede CRUD automaticamente.

**Por que serializers distintos:** evitan asignacion de campos controlados por
servidor y filtran informacion tanto en lectura como en respuestas de escritura.

**Por que PROTECT:** no dejar pedidos sin producto o sucursal. El DELETE del
mantenedor referenciado devuelve un error controlado, no elimina en cascada.

**Precio historico:** se guarda al registrar/cambiar producto. No se recalcula
cuando cambia solo cantidad/estado o el precio del catalogo.

**PUT/PATCH:** PUT requiere los campos obligatorios del contrato; PATCH admite
edicion parcial. El total y precio_unitario no se aceptan desde el cliente.

**Logout y JWT:** logout web termina la sesion web, no revoca JWT. Tokens tienen
vencimiento; cambio de password/desactivacion impiden acceso. No hay blacklist.

**Archivos:** validacion de formato y tamano no equivale a antivirus. Documentos
privados pasan por Django; un alias general de media en Nginx eludiria permisos.

**Limites pendientes:** MySQL temporal requiere permisos de testing; no se
amplian privilegios productivos. El historial Git sensible necesita tratamiento
separado. HTTPS/AWS solo quedan acreditados despues de verificarlos realmente.
