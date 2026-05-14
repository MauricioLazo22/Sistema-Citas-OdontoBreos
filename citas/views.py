"""
Vistas para el modulo de Citas Odontologicas - Grupo D.
RF-01 Registrar, RF-02 Consultar, RF-03 Cancelar.
"""
from datetime import date
from urllib import request

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import (
    CancelarCitaForm,
    ConsultarCitaForm,
    ListarAgendaForm,
    ReasignarCitaForm,
    RegistrarCitaForm,
)
from .models import Cita, Dentista


def menu(request):
    """Menu principal con las opciones del PDF."""
    return render(request, "citas/menu.html")


def registrar(request):
    """RF-01: Registrar Cita Odontologica."""
    if request.method == "POST":
        form = RegistrarCitaForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            with transaction.atomic():
                # Re-chequeo dentro de la transaccion para evitar race conditions
                ocupado = Cita.objects.select_for_update().filter(
                    fecha=datos["fecha"],
                    hora=datos["hora"],
                    dentista=datos["dentista"],
                    estado="Activa",
                ).exists()
                if ocupado:
                    form.add_error(
                        None,
                        "El turno seleccionado no esta disponible para ese dentista.",
                    )
                    return render(request, "citas/registrar.html", {"form": form})

                nuevo_id = Cita.generar_id(datos["fecha"])
                cita = Cita.objects.create(
                    id_cita=nuevo_id,
                    nombre_paciente=datos["nombre_paciente"],
                    dni_paciente=datos["dni_paciente"],
                    telefono=datos["telefono"],
                    fecha=datos["fecha"],
                    hora=datos["hora"],
                    motivo=datos["motivo"],
                    dentista=datos["dentista"],
                    estado="Activa",
                )

            messages.success(
                request,
                f"Cita registrada exitosamente. ID: {cita.id_cita}",
            )
            return redirect("citas:registrar")
    else:
        form = RegistrarCitaForm()

    return render(request, "citas/registrar.html", {"form": form})


def consultar(request):
    """RF-02: Consultar Cita por DNI o Fecha."""
    resultados = None
    realizada = False
    form = ConsultarCitaForm(request.GET or None)

    if request.GET and form.is_valid():
        realizada = True
        criterio = form.cleaned_data["criterio"]
        qs = Cita.objects.select_related("dentista").all()

        if criterio == "1":
            dni = form.cleaned_data["dni"]
            qs = qs.filter(dni_paciente=dni)
        else:
            fecha = form.cleaned_data["fecha"]
            qs = qs.filter(fecha=fecha)

        resultados = qs.order_by("fecha", "hora")

    return render(
        request,
        "citas/consultar.html",
        {
            "form": form,
            "resultados": resultados,
            "realizada": realizada,
        },
    )


def cancelar(request):
    """
    RF-03: Cancelar Cita.
    Flujo:
      1) GET sin parametros: muestra el formulario para ingresar ID.
      2) GET con id_cita: busca y muestra los datos pidiendo confirmacion S/N.
      3) POST: aplica la confirmacion.
    """
    cita = None

    # POST con confirmacion final
    if request.method == "POST":
        form = CancelarCitaForm(request.POST)
        if form.is_valid():
            id_cita = form.cleaned_data["id_cita"]
            confirmacion = form.cleaned_data["confirmacion"]
            try:
                cita = Cita.objects.get(id_cita=id_cita)
            except Cita.DoesNotExist:
                messages.error(
                    request, "No existe ninguna cita con el ID ingresado."
                )
                return redirect("citas:cancelar")

            # En cancelar() — POST
            if not cita.es_cancelable:             
                if cita.estado == "Cancelada":
                    messages.error(request, "La cita ya fue cancelada previamente.")
                else:
                    messages.error(request, "No se pueden cancelar citas de fechas pasadas.")
                return redirect("citas:cancelar")

            if confirmacion == "N":
                messages.info(
                    request, "Operacion cancelada. No se realizaron cambios."
                )
                return redirect("citas:cancelar")

            # confirmacion == "S"
            cita.estado = "Cancelada"
            cita.save(update_fields=["estado", "actualizada_en"])
            messages.success(
                request, f"Cita {cita.id_cita} cancelada exitosamente."
            )
            return redirect("citas:cancelar")
        # form invalido cae al render final con los errores
        return render(
            request,
            "citas/cancelar.html",
            {"form": form, "cita": None, "modo": "confirmar"},
        )

    # GET: puede ser solo formulario o ya con id para mostrar la cita
    id_param = request.GET.get("id_cita", "").strip()
    if id_param:
        from .validators import validar_id_cita
        from django.core.exceptions import ValidationError

        try:
            id_normalizado = validar_id_cita(id_param)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return render(
                request,
                "citas/cancelar.html",
                {"form": None, "cita": None, "modo": "buscar"},
            )

        try:
            cita = Cita.objects.select_related("dentista").get(
                id_cita=id_normalizado
            )
        except Cita.DoesNotExist:
            messages.error(request, "No existe ninguna cita con el ID ingresado.")
            return render(
                request,
                "citas/cancelar.html",
                {"form": None, "cita": None, "modo": "buscar"},
            )

        if cita.estado == "Cancelada":
            messages.error(request, "La cita ya fue cancelada previamente.")
            return render(
                request,
                "citas/cancelar.html",
                {"form": None, "cita": cita, "modo": "buscar"},
            )

        if cita.fecha < date.today():
            messages.error(
                request, "No se pueden cancelar citas de fechas pasadas."
            )
            return render(
                request,
                "citas/cancelar.html",
                {"form": None, "cita": cita, "modo": "buscar"},
            )

        # Mostrar pantalla de confirmacion S/N
        form = CancelarCitaForm(initial={"id_cita": cita.id_cita})
        return render(
            request,
            "citas/cancelar.html",
            {"form": form, "cita": cita, "modo": "confirmar"},
        )

    # GET sin id_cita: solo el formulario inicial
    return render(
        request,
        "citas/cancelar.html",
        {"form": None, "cita": None, "modo": "buscar"},
    )


def reasignar(request):
    """
    RF-04: Reasignar Cita.
    Flujo:
      1) GET sin parametros -> formulario para ingresar ID.
      2) GET con id_cita    -> muestra datos actuales y pide nueva fecha/hora + S/N.
      3) POST               -> aplica el cambio.
    """
    from django.core.exceptions import ValidationError
    from .validators import validar_id_cita

    # POST: confirmacion final
    if request.method == "POST":
        form = ReasignarCitaForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            cita = datos["_cita"]

            if datos["confirmacion"] == "N":
                messages.info(
                    request, "Operacion cancelada. No se realizaron cambios."
                )
                return redirect("citas:reasignar")

            with transaction.atomic():
                # re-chequeo dentro de la transaccion
                ocupado = (
                    Cita.objects.select_for_update()
                    .filter(
                        fecha=datos["nueva_fecha"],
                        hora=datos["nueva_hora"],
                        dentista=cita.dentista,
                        estado="Activa",
                    )
                    .exclude(pk=cita.pk)
                    .exists()
                )
                if ocupado:
                    form.add_error(
                        None,
                        "El nuevo turno no esta disponible para ese dentista.",
                    )
                    return render(
                        request,
                        "citas/reasignar.html",
                        {"form": form, "cita": cita, "modo": "confirmar"},
                    )

                cita.fecha = datos["nueva_fecha"]
                cita.hora = datos["nueva_hora"]
                cita.save(update_fields=["fecha", "hora", "actualizada_en"])

            messages.success(
                request,
                f"Cita {cita.id_cita} reasignada exitosamente a "
                f"{cita.fecha.strftime('%d/%m/%Y')} a las {cita.hora}.",
            )
            return redirect("citas:reasignar")

        # form invalido: re-renderizar pantalla de confirmacion si hay cita
        cita_ctx = form.cleaned_data.get("_cita") if hasattr(form, "cleaned_data") else None
        if not cita_ctx:
            id_post = request.POST.get("id_cita", "").strip().upper()
            try:
                cita_ctx = Cita.objects.select_related("dentista").get(id_cita=id_post)
            except Cita.DoesNotExist:
                cita_ctx = None
        return render(
            request,
            "citas/reasignar.html",
            {"form": form, "cita": cita_ctx, "modo": "confirmar"},
        )

    # GET con id_cita: mostrar datos y pedir nueva fecha/hora
    id_param = request.GET.get("id_cita", "").strip()
    if id_param:
        try:
            id_normalizado = validar_id_cita(id_param)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return render(
                request,
                "citas/reasignar.html",
                {"form": None, "cita": None, "modo": "buscar"},
            )

        try:
            cita = Cita.objects.select_related("dentista").get(
                id_cita=id_normalizado
            )
        except Cita.DoesNotExist:
            messages.error(request, "No existe ninguna cita con el ID ingresado.")
            return render(
                request,
                "citas/reasignar.html",
                {"form": None, "cita": None, "modo": "buscar"},
            )

        if cita.estado == "Cancelada":
            messages.error(request, "No se puede reasignar una cita cancelada.")
            return render(
                request,
                "citas/reasignar.html",
                {"form": None, "cita": cita, "modo": "buscar"},
            )

        form = ReasignarCitaForm(initial={"id_cita": cita.id_cita})
        return render(
            request,
            "citas/reasignar.html",
            {"form": form, "cita": cita, "modo": "confirmar"},
        )

    # GET inicial
    return render(
        request,
        "citas/reasignar.html",
        {"form": None, "cita": None, "modo": "buscar"},
    )


def agenda(request):
    """RF-05: Listar Agenda del Dia o Rango de Fechas."""
    resultados = None
    realizada = False
    fi = ff = None
    dent = None

    form = ListarAgendaForm(request.GET or None)

    if request.GET and form.is_valid():
        realizada = True
        fi = form.cleaned_data["fecha_inicio"]
        ff = form.cleaned_data["fecha_fin"]
        dent = form.cleaned_data.get("dentista")

        qs = Cita.objects.select_related("dentista").filter(
            estado="Activa",
            fecha__gte=fi,
            fecha__lte=ff,
        )
        if dent:
            qs = qs.filter(dentista=dent)
        resultados = qs.order_by("fecha", "hora")

    return render(
        request,
        "citas/agenda.html",
        {
            "form": form,
            "resultados": resultados,
            "realizada": realizada,
            "fecha_inicio": fi,
            "fecha_fin": ff,
            "dentista_seleccionado": dent,
            "total": len(resultados) if resultados is not None else 0,
        },
    )
