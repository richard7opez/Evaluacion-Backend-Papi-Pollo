from rest_framework.permissions import DjangoModelPermissions


class PermisosModelo(DjangoModelPermissions):
    # DRF no exige view_model para GET de forma predeterminada.
    perms_map = {
        **DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
    }


def es_administrador(usuario):
    return usuario.is_authenticated and usuario.is_active and (
        usuario.is_superuser
        or usuario.groups.filter(name="Administrador").exists()
    )
