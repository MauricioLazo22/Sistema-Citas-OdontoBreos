from django.contrib import admin
from .models import Cita, Dentista


@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)
