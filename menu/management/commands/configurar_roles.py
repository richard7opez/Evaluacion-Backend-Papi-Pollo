from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q


ROLES = {
    "Administrador": ("add", "change", "delete", "view"),
    "Operador": ("add", "change", "view"),
    "Consulta": ("view",),
}


class Command(BaseCommand):
    help = "Configura perfiles, asigna usuarios y permite crearlos con contraseña interactiva."

    def add_arguments(self, parser):
        parser.add_argument("--usuario")
        parser.add_argument("--rol", choices=ROLES)
        parser.add_argument("--crear", action="store_true", help="Crea un usuario nuevo y solicita su contraseña sin mostrarla.")

    @transaction.atomic
    def handle(self, *args, **options):
        if bool(options["usuario"]) != bool(options["rol"]):
            raise CommandError("Indica --usuario y --rol juntos.")
        if options["crear"] and not options["usuario"]:
            raise CommandError("Para crear un usuario indica --usuario y --rol.")
        nuevo_usuario = None
        if options["crear"]:
            User = get_user_model()
            nombre = options["usuario"]
            if User.objects.filter(**{User.USERNAME_FIELD: nombre}).exists():
                raise CommandError("El usuario ya existe. No se ha cambiado su contraseña.")
            nuevo_usuario = User(**{User.USERNAME_FIELD: nombre})
            try:
                User._meta.get_field(User.USERNAME_FIELD).clean(nombre, nuevo_usuario)
                password = getpass("Contraseña del nuevo usuario: ")
                confirmacion = getpass("Repite la contraseña: ")
                if password != confirmacion:
                    raise CommandError("Las contraseñas no coinciden. No se creó el usuario.")
                validate_password(password, nuevo_usuario)
            except ValidationError as error:
                raise CommandError(" ".join(error.messages))
            except (EOFError, KeyboardInterrupt):
                raise CommandError("Creación cancelada. No se creó el usuario.")
            nuevo_usuario.set_password(password)
        for nombre, acciones in ROLES.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            consulta = Q()
            for app, modelo in (("menu", "producto"), ("menu", "pedido"), ("sucursales", "sucursal")):
                consulta |= Q(content_type__app_label=app, codename__in=[f"{a}_{modelo}" for a in acciones])
            if nombre == "Administrador":
                consulta |= Q(content_type__app_label="auth", content_type__model__in=("user", "group"))
            grupo.permissions.set(Permission.objects.filter(consulta))
        if options["usuario"]:
            User = get_user_model()
            if nuevo_usuario is not None:
                nuevo_usuario.save()
                usuario = nuevo_usuario
            else:
                try:
                    usuario = User.objects.get(**{User.USERNAME_FIELD: options["usuario"]})
                except User.DoesNotExist:
                    raise CommandError("El usuario no existe; usa --crear o créalo desde Django Admin.")
            if usuario.is_superuser and options["rol"] != "Administrador":
                raise CommandError("Un superusuario no puede usarse para probar un rol restringido.")
            usuario.groups.remove(*Group.objects.filter(name__in=ROLES))
            usuario.groups.add(Group.objects.get(name=options["rol"]))
            usuario.is_staff = options["rol"] == "Administrador"
            usuario.save(update_fields=["is_staff"])
            self.stdout.write(self.style.SUCCESS(f"Perfil asignado a {options['usuario']}."))
        self.stdout.write(self.style.SUCCESS("Perfiles configurados."))

