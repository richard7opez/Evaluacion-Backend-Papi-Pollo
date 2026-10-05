from django import forms
from django.core.exceptions import ValidationError

from .models import Producto, Pedido


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css = "form-select"
            else:
                css = "form-control"
            field.widget.attrs["class"] = css
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3


class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = ("nombre", "descripcion", "precio", "categoria", "disponible", "imagen", "ficha_tecnica")

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if imagen and hasattr(imagen, "content_type") and imagen.size > 5 * 1024 * 1024:
            raise ValidationError("La imagen no puede superar 5 MB.")
        return imagen

    def clean_ficha_tecnica(self):
        archivo = self.cleaned_data.get("ficha_tecnica")
        if archivo and hasattr(archivo, "content_type"):
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError("El documento no puede superar 10 MB.")
            if not archivo.name.lower().endswith(".pdf") or archivo.read(5) != b"%PDF-":
                archivo.seek(0)
                raise ValidationError("Adjunta una ficha técnica en formato PDF.")
            archivo.seek(0)
        return archivo


class PedidoForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].empty_label = "Selecciona un producto"
        self.fields["sucursal"].empty_label = "Selecciona una sucursal"

    class Meta:
        model = Pedido
        fields = ("cliente", "producto", "sucursal", "cantidad", "estado", "observaciones")

