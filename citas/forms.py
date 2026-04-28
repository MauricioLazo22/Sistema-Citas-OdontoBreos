"""
Formularios para RF-01, RF-02, RF-03.
Hacen toda la validacion estricta especificada en el PDF.
"""
from datetime import date, datetime

from django import forms
from django.core.exceptions import ValidationError

from . import validators
from .models import Cita, Dentista, HORAS_DISPONIBLES, MOTIVOS

