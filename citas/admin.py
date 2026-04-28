from django.contrib import admin
from .models import Cita, Dentista


@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "id_cita",
        "nombre_paciente",
        "dni_paciente",
        "fecha",
        "hora",
        "dentista",
        "estado",
    )
    list_filter = ("estado", "fecha", "dentista")
    search_fields = ("id_cita", "dni_paciente", "nombre_paciente")
    readonly_fields = ("id_cita", "creada_en", "actualizada_en")
