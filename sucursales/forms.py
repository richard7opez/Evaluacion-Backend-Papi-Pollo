from django import forms
from menu.forms import BootstrapFormMixin
from .models import Sucursal


class SucursalForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ("nombre", "direccion", "comuna", "telefono", "horario", "activa")

