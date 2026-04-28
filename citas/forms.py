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