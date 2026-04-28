"""
Formularios para RF-01, RF-02, RF-03.
Hacen toda la validacion estricta especificada en el PDF.
"""
from datetime import date, datetime

from django import forms
from django.core.exceptions import ValidationError

from . import validators
from .models import Cita, Dentista, HORAS_DISPONIBLES, MOTIVOS

class RegistrarCitaForm(forms.Form):
    """RF-01: Registrar Cita."""

    nombre_paciente = forms.CharField(
        label="Nombre completo del paciente",
        max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "Solo letras y espacios"}),
    )
    dni_paciente = forms.CharField(
        label="DNI",
        max_length=8,
        widget=forms.TextInput(attrs={"placeholder": "8 digitos", "inputmode": "numeric"}),
    )
    telefono = forms.CharField(
        label="Telefono",
        max_length=9,
        widget=forms.TextInput(attrs={"placeholder": "9 digitos", "inputmode": "numeric"}),
    )
    fecha = forms.CharField(
        label="Fecha (DD/MM/AAAA)",
        widget=forms.TextInput(attrs={"placeholder": "DD/MM/AAAA"}),
    )
    hora = forms.ChoiceField(label="Hora", choices=HORAS_DISPONIBLES)
    motivo = forms.ChoiceField(label="Motivo de consulta", choices=MOTIVOS)
    dentista = forms.ModelChoiceField(
        label="Dentista",
        queryset=Dentista.objects.filter(activo=True).order_by("nombre"),
        empty_label="-- Seleccione --",
    )

    # ---- field-level cleans ----
    def clean_nombre_paciente(self):
        return validators.validar_nombre(self.cleaned_data.get("nombre_paciente"))

    def clean_dni_paciente(self):
        return validators.validar_dni(self.cleaned_data.get("dni_paciente"))

    def clean_telefono(self):
        return validators.validar_telefono(self.cleaned_data.get("telefono"))

    def clean_fecha(self):
        f = validators.parsear_fecha_ddmmaaaa(self.cleaned_data.get("fecha"))
        return validators.validar_fecha_cita(f)

    def clean_hora(self):
        return validators.validar_hora(self.cleaned_data.get("hora"))

    def clean_motivo(self):
        return validators.validar_motivo(self.cleaned_data.get("motivo"))

    # ---- cross-field clean ----
    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get("fecha")
        hora = cleaned.get("hora")
        dentista = cleaned.get("dentista")
        dni = cleaned.get("dni_paciente")

        if fecha and hora and dentista:
            ocupado = Cita.objects.filter(
                fecha=fecha,
                hora=hora,
                dentista=dentista,
                estado="Activa",
            ).exists()
            if ocupado:
                raise ValidationError(
                    "El turno seleccionado no esta disponible para ese dentista."
                )

        if fecha and dni:
            duplicado = Cita.objects.filter(
                fecha=fecha,
                dni_paciente=dni,
                estado="Activa",
            ).exists()
            if duplicado:
                raise ValidationError(
                    "El paciente ya tiene una cita registrada para esa fecha."
                )

        return cleaned


class ConsultarCitaForm(forms.Form):
    """RF-02: Consultar Cita por DNI o Fecha."""

    CRITERIOS = [
        ("1", "Por DNI"),
        ("2", "Por Fecha"),
    ]

    criterio = forms.ChoiceField(label="Criterio de busqueda", choices=CRITERIOS)
    dni = forms.CharField(label="DNI (8 digitos)", max_length=8, required=False)
    fecha = forms.CharField(label="Fecha (DD/MM/AAAA)", required=False)

    def clean(self):
        cleaned = super().clean()
        criterio = cleaned.get("criterio")

        if criterio not in {"1", "2"}:
            raise ValidationError("Opcion invalida. Seleccione 1 (DNI) o 2 (Fecha).")

        if criterio == "1":
            dni = cleaned.get("dni")
            if not dni:
                raise ValidationError("Debe ingresar el DNI para buscar.")
            cleaned["dni"] = validators.validar_dni(dni)
            cleaned["fecha"] = None
        else:  # criterio == "2"
            fecha_str = cleaned.get("fecha")
            if not fecha_str:
                raise ValidationError("Debe ingresar la fecha para buscar.")
            cleaned["fecha"] = validators.parsear_fecha_ddmmaaaa(fecha_str)
            cleaned["dni"] = None

        return cleaned
