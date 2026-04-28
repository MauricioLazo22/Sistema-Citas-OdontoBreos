"""
Validaciones reutilizables que cumplen al pie de la letra el PDF de
requerimientos del Grupo D (RF-01, RF-02, RF-03).
"""
import re
from datetime import date, datetime

from django.core.exceptions import ValidationError


RE_SOLO_LETRAS = re.compile(
    r"^[A-Za-záéíóúÁÉÍÓÚñÑüÜ ]+$"
)
RE_DIGITOS_8 = re.compile(r"^\d{8}$")
RE_DIGITOS_9 = re.compile(r"^\d{9}$")
RE_ID_CITA = re.compile(r"^CIT-\d{8}-\d{3}$")

HORAS_VALIDAS = {"08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"}
MOTIVOS_VALIDOS = {"Limpieza", "Extraccion", "Endodoncia", "Ortodoncia", "Revision general"}


def validar_nombre(nombre):
    """Solo letras y espacios, maximo 80 caracteres."""
    if not nombre:
        raise ValidationError("El campo Nombre es obligatorio.")
    nombre = nombre.strip()
    if len(nombre) == 0:
        raise ValidationError("El campo Nombre es obligatorio.")
    if len(nombre) > 80:
        raise ValidationError("El nombre no puede superar 80 caracteres.")
    if not RE_SOLO_LETRAS.match(nombre):
        raise ValidationError("El nombre solo puede contener letras y espacios.")
    return nombre


def validar_dni(dni):
    """Exactamente 8 digitos numericos."""
    if dni is None or dni == "":
        raise ValidationError("El campo DNI es obligatorio.")
    dni = str(dni).strip()
    if not RE_DIGITOS_8.match(dni):
        raise ValidationError("DNI invalido. Ingrese exactamente 8 digitos.")
    return dni


def validar_telefono(telefono):
    """Exactamente 9 digitos numericos."""
    if telefono is None or telefono == "":
        raise ValidationError("El campo Telefono es obligatorio.")
    telefono = str(telefono).strip()
    if not RE_DIGITOS_9.match(telefono):
        raise ValidationError("Telefono invalido. Ingrese exactamente 9 digitos.")
    return telefono


def parsear_fecha_ddmmaaaa(fecha_str):
    """Parsea DD/MM/AAAA. Lanza ValidationError con el mensaje del PDF."""
    if not fecha_str:
        raise ValidationError("El campo Fecha es obligatorio.")
    fecha_str = str(fecha_str).strip()
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError("Formato de fecha invalido. Use DD/MM/AAAA.")


def validar_fecha_cita(f):
    """No puede ser fecha pasada ni domingo."""
    if isinstance(f, str):
        f = parsear_fecha_ddmmaaaa(f)
    hoy = date.today()
    if f < hoy:
        raise ValidationError("No se pueden registrar citas en fechas pasadas.")
    if f.weekday() == 6:  # 6 = domingo
        raise ValidationError("No se atiende los domingos.")
    return f


def validar_hora(hora):
    if not hora:
        raise ValidationError("El campo Hora es obligatorio.")
    hora = str(hora).strip()
    if hora not in HORAS_VALIDAS:
        raise ValidationError(
            "Hora invalida. Turnos validos: 08:00, 09:00, 10:00, 11:00, "
            "14:00, 15:00, 16:00, 17:00."
        )
    return hora


def validar_motivo(motivo):
    if not motivo:
        raise ValidationError("El campo Motivo es obligatorio.")
    motivo = str(motivo).strip()
    if motivo not in MOTIVOS_VALIDOS:
        raise ValidationError("Motivo de consulta no valido.")
    return motivo


def validar_id_cita(id_cita):
    if not id_cita:
        raise ValidationError("El campo ID de cita es obligatorio.")
    id_cita = str(id_cita).strip().upper()
    if not RE_ID_CITA.match(id_cita):
        raise ValidationError("Formato de ID invalido. Use CIT-YYYYMMDD-NNN.")
    return id_cita
