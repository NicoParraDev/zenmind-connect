"""
Módulo de reservas y gestión de psicólogos.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from core.models import Especialidad, Psicologo, Horarios, Agenda, HorarioAgenda, Persona, VideoCallRoom
from core.forms import PsicologoForm, EspecialidadForm, HorariosForm, AgendaForm
from core.decorators import rate_limit, rate_limit_by_username
from core.security import ip_esta_bloqueada, validar_tipo_archivo, registrar_intento_sospechoso
from django.contrib.auth.models import User
import os
import logging

logger = logging.getLogger(__name__)


def generar_pdf_comprobante(persona, agenda, horario_agenda):
    """
    Genera un PDF del comprobante de reserva.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4A90E2'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.textColor = colors.HexColor('#2C3E50')
    
    # Contenido del PDF
    story = []
    
    # Título
    story.append(Paragraph("ZenMindConnect", title_style))
    story.append(Paragraph("Comprobante de Reserva", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Información del Paciente
    story.append(Paragraph("Información del Paciente", heading_style))
    paciente_data = [
        ['Nombre Completo:', f"{persona.nombre} {persona.apellido}"],
        ['RUT:', persona.rut],
        ['Email:', persona.correo],
        ['Teléfono:', persona.telefono],
    ]
    paciente_table = Table(paciente_data, colWidths=[2*inch, 4*inch])
    paciente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
    ]))
    story.append(paciente_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Detalles de la Cita
    story.append(Paragraph("Detalles de la Cita", heading_style))
    cita_data = [
        ['Psicólogo:', agenda.psicologo.nombre],
        ['Especialidad:', str(agenda.psicologo.especialidad)],
        ['Fecha:', agenda.data.strftime('%d/%m/%Y')],
        ['Horario Reservado:', horario_agenda.horario.horas],
    ]
    cita_table = Table(cita_data, colWidths=[2*inch, 4*inch])
    cita_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
    ]))
    story.append(cita_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Información de Contacto
    story.append(Paragraph("Información de Contacto", heading_style))
    contacto_data = [
        ['Email del Psicólogo:', agenda.psicologo.email],
        ['Teléfono del Psicólogo:', agenda.psicologo.telefono],
    ]
    contacto_table = Table(contacto_data, colWidths=[2*inch, 4*inch])
    contacto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
    ]))
    story.append(contacto_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Mensaje final
    mensaje = Paragraph(
        "<b>Reserva Confirmada!</b> Tu cita ha sido agendada correctamente. "
        "Recibirás un recordatorio antes de la fecha programada.",
        normal_style
    )
    story.append(mensaje)
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def send_reservation_email(persona, agenda, horario_agenda):
    """
    Envía el comprobante de reserva por correo electrónico.
    """
    try:
        # Generar PDF
        pdf_buffer = generar_pdf_comprobante(persona, agenda, horario_agenda)
        
        # Preparar el correo
        subject = f'Comprobante de Reserva - ZenMindConnect | Reserva #{agenda.id}'
        
        # Cuerpo del mensaje HTML
        html_message = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        background: linear-gradient(to bottom, #4b908e, #ffffff, #4b908e);
                        color: #fff;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: linear-gradient(to bottom, #4b908e, #ffffff, #4b908e);
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }}
                    h1 {{
                        color: #808080;
                    }}
                    p {{
                        color: #000;
                        font-size: 16px;
                        line-height: 1.5;
                        margin-bottom: 20px;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        margin-bottom: 20px;
                    }}
                    .zenmindconnect-text {{
                        color: #001F3F;
                        font-size: 36px;
                        font-weight: bold;
                        margin-top: 10px;
                    }}
                    .info-box {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                        text-align: left;
                    }}
                    .info-box p {{
                        margin: 5px 0;
                        color: #2C3E50;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <img src="https://i.postimg.cc/RCWybCKM/logo-final.png" alt="Logo de ZenMindConnect">
                    <div class="zenmindconnect-text">ZenMindConnect</div>
                    <h1>¡Cita Reservada Exitosamente!</h1>
                    <p>Hola <strong>{persona.nombre} {persona.apellido}</strong>,</p>
                    <p>Tu reserva ha sido confirmada. Adjuntamos el comprobante en formato PDF.</p>
                    
                    <div class="info-box">
                        <p><strong>Psicólogo:</strong> {agenda.psicologo.nombre}</p>
                        <p><strong>Especialidad:</strong> {agenda.psicologo.especialidad}</p>
                        <p><strong>Fecha:</strong> {agenda.data.strftime('%d/%m/%Y')}</p>
                        <p><strong>Horario:</strong> {horario_agenda.horario.horas}</p>
                    </div>
                    
                    <p>Recibirás un recordatorio antes de la fecha programada.</p>
                    <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
                </div>
            </body>
        </html>
        """
        
        # Crear el mensaje de correo
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[persona.correo],
        )
        email.content_subtype = "html"
        
        # Adjuntar PDF
        email.attach(
            f'comprobante_reserva_{agenda.id}.pdf',
            pdf_buffer.getvalue(),
            'application/pdf'
        )
        
        # Enviar correo
        email.send()
        logger.info(f"Comprobante enviado por correo a {persona.correo}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar comprobante por correo: {e}")
        return False




def listar_agendas(request):
    """
    Lista las agendas agrupadas por psicólogo con filtros y búsqueda.
    Optimizada con annotate para evitar N+1 queries.
    Solo muestra agendas futuras o del día actual.
    """
    from django.db.models import Count, Q
    from datetime import date
    
    # Obtener todas las agendas con sus relaciones optimizadas
    # Filtrar solo agendas futuras (>= hoy) para evitar mostrar fechas pasadas
    hoy = date.today()
    agendas = Agenda.objects.select_related('psicologo', 'psicologo__especialidad').prefetch_related('horarioagenda_set').filter(data__gte=hoy).order_by('psicologo__nombre', 'data')
    
    # Filtros
    especialidad_id = request.GET.get('especialidad')
    busqueda = request.GET.get('q', '').strip()
    
    if especialidad_id:
        agendas = agendas.filter(psicologo__especialidad_id=especialidad_id)
    
    if busqueda:
        agendas = agendas.filter(
            Q(psicologo__nombre__icontains=busqueda) |
            Q(psicologo__especialidad__nombre__icontains=busqueda)
        )
    
    # Optimizar con annotate para contar horarios disponibles (evita N+1 queries)
    agendas_optimizadas = agendas.annotate(
        total_horarios_disponibles=Count(
            'horarioagenda',
            filter=Q(horarioagenda__reservado_por__isnull=True)
        )
    )
    
    # Agrupar agendas por psicólogo
    psicologos_agendas = {}
    for agenda in agendas_optimizadas:
        psicologo_id = agenda.psicologo.id
        if psicologo_id not in psicologos_agendas:
            psicologos_agendas[psicologo_id] = {
                'psicologo': agenda.psicologo,
                'agendas': [],
                'total_fechas': 0,
                'total_horarios_disponibles': 0
            }
        psicologos_agendas[psicologo_id]['agendas'].append(agenda)
        psicologos_agendas[psicologo_id]['total_fechas'] += 1
        psicologos_agendas[psicologo_id]['total_horarios_disponibles'] += agenda.total_horarios_disponibles
    
    # Obtener especialidades para el filtro
    from core.models import Especialidad
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    context = {
        'psicologos_agendas': psicologos_agendas.values(),
        'especialidades': especialidades,
        'especialidad_seleccionada': int(especialidad_id) if especialidad_id else None,
        'busqueda': busqueda,
        'total_psicologos': len(psicologos_agendas),
        'total_agendas': agendas.count()
    }
    
    return render(request, 'core/listar_agendas.html', context)

def detallar_agenda(request, id):
    """
    Muestra el detalle de una agenda con sus horarios disponibles y reservados.
    Solo muestra agendas futuras o del día actual.
    """
    from datetime import date
    
    # Optimizar la consulta para incluir los horarios y horarios de agenda
    agenda = get_object_or_404(
        Agenda.objects.select_related('psicologo', 'psicologo__especialidad')
                      .prefetch_related('horarioagenda_set__horario', 'horarioagenda_set__reservado_por'),
        pk=id
    )
    
    # Verificar que la agenda no sea del pasado
    if agenda.data < date.today():
        messages.warning(request, "Esta agenda corresponde a una fecha que ya pasó.")
        return redirect('listar_agendas')
    
    # Obtener horarios disponibles y reservados
    horarios_disponibles = agenda.get_horarios_disponibles().select_related('horario')
    horarios_reservados = agenda.get_horarios_reservados().select_related('horario', 'reservado_por')
    
    context = {
        'agenda': agenda,
        'horarios_disponibles': horarios_disponibles,
        'horarios_reservados': horarios_reservados,
    }
    return render(request, 'core/detallar_agenda.html', context)

def comprobante_reserva(request, id):
    """
    Vista para mostrar el comprobante de reserva de cita.
    """
    # Optimizar la consulta
    agenda = get_object_or_404(
        Agenda.objects.select_related('psicologo', 'psicologo__especialidad').prefetch_related('horarios'),
        pk=id
    )
    
    # Obtener la persona del usuario autenticado
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para ver el comprobante.")
        return redirect('log')
    
    try:
        persona = request.user.persona
    except Persona.DoesNotExist:
        messages.error(request, "Tu perfil de usuario no está completo.")
        return redirect('form_persona')
    
    # Verificar que el usuario tenga esta consulta reservada
    if agenda not in persona.consulta.all():
        messages.warning(request, "Esta reserva no está asociada a tu cuenta.")
        return redirect('listar_agendas')
    
    # Obtener el horario reservado por este usuario
    horario_reservado = HorarioAgenda.objects.filter(
        agenda=agenda,
        reservado_por=persona
    ).select_related('horario').first()
    
    context = {
        'agenda': agenda,
        'persona': persona,
        'horario_reservado': horario_reservado,
    }
    return render(request, 'core/comprobante_reserva.html', context)


@login_required
def descargar_comprobante_pdf(request, id):
    """
    Vista para descargar el comprobante de reserva en formato PDF.
    """
    # Optimizar la consulta
    agenda = get_object_or_404(
        Agenda.objects.select_related('psicologo', 'psicologo__especialidad'),
        pk=id
    )
    
    # Obtener la persona del usuario autenticado
    try:
        persona = request.user.persona
    except Persona.DoesNotExist:
        messages.error(request, "Tu perfil de usuario no está completo.")
        return redirect('form_persona')
    
    # Verificar que el usuario tenga esta consulta reservada
    if agenda not in persona.consulta.all():
        messages.warning(request, "Esta reserva no está asociada a tu cuenta.")
        return redirect('listar_agendas')
    
    # Obtener el horario reservado por este usuario
    horario_reservado = HorarioAgenda.objects.filter(
        agenda=agenda,
        reservado_por=persona
    ).select_related('horario').first()
    
    if not horario_reservado:
        messages.error(request, "No se encontró el horario reservado.")
        return redirect('comprobante_reserva', id=agenda.id)
    
    # Generar PDF
    pdf_buffer = generar_pdf_comprobante(persona, agenda, horario_reservado)
    
    # Crear respuesta HTTP con el PDF
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_reserva_{agenda.id}.pdf"'
    
    return response

@login_required
def marcar_consulta(request, id):
    """
    Reserva un horario específico de una agenda para el usuario autenticado.
    Usa transacciones atómicas para evitar condiciones de carrera.
    """
    from django.db import transaction
    from datetime import date
    
    agenda = get_object_or_404(
        Agenda.objects.select_related('psicologo').prefetch_related('horarioagenda_set__horario'),
        pk=id
    )
    
    # Verificar que la agenda no sea del pasado
    if agenda.data < date.today():
        messages.error(request, "No puedes reservar una cita en una fecha que ya pasó.")
        return redirect('listar_agendas')
    
    # Verificar que el usuario esté autenticado y tenga un perfil Persona
    try:
        persona = request.user.persona
    except Persona.DoesNotExist:
        messages.error(request, "Tu perfil de usuario no está completo. Por favor, completa tu perfil.")
        return redirect('form_persona')
    
    # Obtener el ID del horario desde el POST
    horario_id = request.POST.get('horario_id')
    
    if not horario_id:
        messages.error(request, "Debes seleccionar un horario para reservar.")
        return redirect('detallar_agenda', id=agenda.id)
    
    # Usar transacción atómica para evitar condiciones de carrera
    try:
        with transaction.atomic():
            # Verificar primero si el usuario ya tiene una reserva en esta agenda
            if HorarioAgenda.objects.filter(agenda=agenda, reservado_por=persona).exists():
                messages.warning(request, "Ya tienes una cita reservada en esta agenda.")
                return redirect('listar_agendas')
            
            # Buscar el HorarioAgenda específico y bloquearlo para actualización
            # select_for_update() previene condiciones de carrera
            horario_agenda = HorarioAgenda.objects.select_for_update().get(
                agenda=agenda,
                id=horario_id,
                reservado_por__isnull=True  # Solo si está disponible
            )
            
            # Reservar el horario
            horario_agenda.reservado_por = persona
            horario_agenda.save()
            
            # También agregar la agenda a las consultas del paciente (para compatibilidad)
            persona.consulta.add(agenda)
            
    except HorarioAgenda.DoesNotExist:
        messages.error(request, "El horario seleccionado no está disponible o ya fue reservado.")
        return redirect('detallar_agenda', id=agenda.id)
    except Exception as e:
        logger.error(f"Error al reservar horario: {e}", exc_info=True)
        messages.error(request, "Ocurrió un error al procesar tu reserva. Por favor, intenta nuevamente.")
        return redirect('detallar_agenda', id=agenda.id)
    
    # Enviar comprobante por correo
    try:
        send_reservation_email(persona, agenda, horario_agenda)
    except Exception as e:
        # No fallar la reserva si el correo falla, solo loguear
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al enviar correo de comprobante: {e}")
    
    messages.success(
        request, 
        f"¡Cita reservada exitosamente con {agenda.psicologo.nombre} para el {agenda.data} a las {horario_agenda.horario.horas}!"
    )
    
    # Redirigir a la página de comprobante de reserva
    return redirect('comprobante_reserva', id=agenda.id)
    
    









    ###### Reserva de hora ######
@login_required
def registrar_especialidad(request):
    """
    Vista para registrar una nueva especialidad.
    Requiere autenticación y permisos de superusuario.
    """
    # Verificar que sea superusuario
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect('index')
    
    # Verificar si la IP está bloqueada
    if ip_esta_bloqueada(request):
        messages.error(request, "Tu IP ha sido bloqueada por intentos de ataque.")
        return redirect('index')
    
    if request.method == "POST":
        form = EspecialidadForm(request.POST, request.FILES)
        form.request = request  # Para logging de seguridad
        if form.is_valid():
            especialidad = form.save(commit=False)
            form.save()
            logger.info(f"Especialidad '{especialidad.nombre}' creada por {request.user.username}")
            messages.success(request, "¡Especialidad registrada exitosamente!")
            return redirect('registrar_especialidad')
    else:
        form = EspecialidadForm() 
    
    return render(request,'core/registrar_especialidad.html', {'form': form})





@login_required
def registrar_psicologo(request):
    """
    Vista para registrar un nuevo psicólogo.
    Requiere autenticación y permisos de superusuario.
    """
    # Verificar que sea superusuario
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect('index')
    
    # Verificar si la IP está bloqueada
    if ip_esta_bloqueada(request):
        messages.error(request, "Tu IP ha sido bloqueada por intentos de ataque.")
        return redirect('index')
    
    if request.method == "POST":
        # Validar archivos si existen
        if request.FILES:
            for field_name, archivo in request.FILES.items():
                es_valido, mensaje = validar_tipo_archivo(archivo)
                if not es_valido:
                    registrar_intento_sospechoso(
                        request,
                        "FILE_UPLOAD_ATTACK",
                        f"Archivo sospechoso: {archivo.name}, tipo: {archivo.content_type}"
                    )
                    messages.error(request, mensaje)
                    return redirect('adm')
        
        form = PsicologoForm(request.POST, request.FILES)
        form.request = request  # Para logging de seguridad
        if form.is_valid():
            psicologo = form.save(commit=False)
            form.save()
            logger.info(f"Psicólogo '{psicologo.nombre}' creado por {request.user.username}")
            messages.success(request, "¡Psicólogo registrado exitosamente!")
            return redirect('registrar_psicologo')
    else:
        form = PsicologoForm()

    return render(request, 'core/registrar_psicologo.html', {'form': form})

@login_required
def insertar_horarios(request):
    """
    Vista para insertar nuevos horarios.
    Requiere autenticación y permisos de superusuario.
    """
    # Verificar que sea superusuario
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect('index')
    
    # Verificar si la IP está bloqueada
    if ip_esta_bloqueada(request):
        messages.error(request, "Tu IP ha sido bloqueada por intentos de ataque.")
        return redirect('index')
    
    if request.method == 'POST':
        form = HorariosForm(request.POST, request.FILES)
        form.request = request  # Para logging de seguridad
        if form.is_valid():
            horarios = form.save(commit=False)
            form.save()
            logger.info(f"Horario '{horarios.horas}' creado por {request.user.username}")
            messages.success(request, "¡Horario registrado exitosamente!")
            return redirect('insertar_horarios')
    else:
        form = HorariosForm()
    return render(request, 'core/insertar_horarios.html',{'form':form})

@login_required
def crear_nueva_agenda(request):
    """
    Crea una nueva agenda y automáticamente crea los HorarioAgenda para cada horario seleccionado.
    Requiere autenticación y permisos de superusuario.
    Usa transacciones para garantizar consistencia.
    """
    from django.db import transaction
    
    # Verificar que sea superusuario
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect('index')
    
    # Verificar si la IP está bloqueada
    if ip_esta_bloqueada(request):
        messages.error(request, "Tu IP ha sido bloqueada por intentos de ataque.")
        return redirect('index')
    
    if request.method == "POST":
        form = AgendaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    agenda = form.save(commit=False)
                    agenda.save()  # Guardar primero la agenda
                    
                    # Obtener los horarios seleccionados del formulario
                    horarios_seleccionados = form.cleaned_data.get('horarios', [])
                    
                    if not horarios_seleccionados:
                        messages.error(request, "Debes seleccionar al menos un horario para la agenda.")
                        return render(request, 'core/crear_nueva_agenda.html', {'form': form})
                    
                    # Crear un HorarioAgenda para cada horario seleccionado
                    # Usar get_or_create para evitar duplicados, pero manejar errores
                    horarios_creados = []
                    for horario in horarios_seleccionados:
                        horario_agenda, created = HorarioAgenda.objects.get_or_create(
                            agenda=agenda,
                            horario=horario,
                            defaults={'reservado_por': None}
                        )
                        horarios_creados.append(horario_agenda)
                    
                    logger.info(
                        f"Agenda creada: {agenda.psicologo.nombre} - {agenda.data} "
                        f"con {len(horarios_creados)} horarios por {request.user.username}"
                    )
                    
                messages.success(
                    request, 
                    f"¡Agenda creada exitosamente para {agenda.psicologo.nombre} el {agenda.data} "
                    f"con {len(horarios_creados)} horario(s)!"
                )
                return redirect('listar_agendas')
            except Exception as e:
                logger.error(f"Error al crear agenda: {e}", exc_info=True)
                messages.error(request, "Ocurrió un error al crear la agenda. Por favor, intenta nuevamente.")
    else:
        form = AgendaForm()
    return render(request, 'core/crear_nueva_agenda.html', {'form': form})

























@login_required
def adm(request):
    """
    Vista del panel de administración.
    Requiere autenticación y permisos de superusuario.
    """
    # Verificar que sea superusuario
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect('index')
    
    # Verificar si la IP está bloqueada
    if ip_esta_bloqueada(request):
        messages.error(request, "Tu IP ha sido bloqueada por intentos de ataque.")
        return redirect('index')
    
    return render(request,'core/administracion.html')

@login_required
def area_de_persona(request, id):
    """
    Muestra el área personal del usuario con sus citas reservadas.
    """
    persona = get_object_or_404(
        Persona.objects.select_related('tipousuario', 'user'),
        id=id
    )
    
    # Verificar que el usuario tenga acceso a este perfil
    if request.user.persona != persona and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a este perfil.")
        return redirect('index')
    
    # Obtener todas las reservas con sus horarios
    reservas_query = HorarioAgenda.objects.filter(
        reservado_por=persona
    ).select_related('agenda', 'agenda__psicologo', 'agenda__psicologo__especialidad', 'horario').order_by('agenda__data', 'horario__horas')
    
    # Paginación: 5 citas por página
    paginator = Paginator(reservas_query, 5)
    page = request.GET.get('page', 1)
    
    try:
        reservas_page = paginator.page(page)
    except PageNotAnInteger:
        reservas_page = paginator.page(1)
    except EmptyPage:
        reservas_page = paginator.page(paginator.num_pages)
    
    # Obtener salas activas para cada reserva en la página actual
    reservas_con_salas = []
    for reserva in reservas_page:
        # Buscar si hay una sala activa para esta agenda/horario
        sala_activa = None
        if reserva.agenda:
            salas = VideoCallRoom.objects.filter(
                agenda=reserva.agenda,
                is_active=True
            ).order_by('-created_at')
            
            # Buscar sala que coincida con este horario específico
            for sala in salas:
                if str(reserva.id) in sala.name:
                    sala_activa = sala
                    break
        
        reservas_con_salas.append({
            'reserva': reserva,
            'sala_activa': sala_activa
        })
    
    return render(request, 'core/area_de_persona.html', {
        'persona': persona,
        'reservas': reservas_con_salas,
        'paginator': paginator,
        'page_obj': reservas_page
    })

@login_required
def cancelar_cita(request, id):
    """
    Cancela una cita reservada por el usuario.
    Usa transacciones atómicas para garantizar consistencia.
    """
    from datetime import date, datetime
    from django.db import transaction
    
    # Obtener el horario reservado
    horario_agenda = get_object_or_404(
        HorarioAgenda.objects.select_related('agenda', 'agenda__psicologo', 'horario', 'reservado_por'),
        pk=id
    )
    
    # Verificar que el usuario esté autenticado y tenga un perfil Persona
    try:
        persona = request.user.persona
    except Persona.DoesNotExist:
        messages.error(request, "Tu perfil de usuario no está completo.")
        return redirect('form_persona')
    
    # Verificar que el horario pertenezca al usuario
    if horario_agenda.reservado_por != persona:
        messages.error(request, "No tienes permiso para cancelar esta cita.")
        return redirect('autenticar_persona')
    
    # Verificar que la cita no sea del pasado (usando función centralizada)
    from .helpers import validar_cita_puede_modificarse
    try:
        validar_cita_puede_modificarse(horario_agenda)
    except ValidationError as e:
        messages.warning(request, str(e))
        return redirect('autenticar_persona')
    
    # Obtener información antes de cancelar (para el mensaje)
    agenda = horario_agenda.agenda
    horario = horario_agenda.horario
    
    # Usar transacción atómica para garantizar consistencia
    try:
        with transaction.atomic():
            # Cancelar la reserva
            horario_agenda.reservado_por = None
            horario_agenda.save()
            
            # Remover la agenda de las consultas del paciente si no tiene más horarios reservados
            if not HorarioAgenda.objects.filter(agenda=agenda, reservado_por=persona).exists():
                persona.consulta.remove(agenda)
            
            logger.info(
                f"Cita cancelada: Usuario {persona.rut} canceló horario "
                f"{horario.horas} en agenda {agenda.id} ({agenda.data})"
            )
    except Exception as e:
        logger.error(f"Error al cancelar cita: {e}", exc_info=True)
        messages.error(request, "Ocurrió un error al cancelar la cita. Por favor, intenta nuevamente.")
        return redirect('autenticar_persona')
    
    messages.success(
        request,
        f"¡Cita cancelada exitosamente! Tu reserva con {agenda.psicologo.nombre} para el {agenda.data} a las {horario.horas} ha sido cancelada."
    )
    
    return redirect('autenticar_persona')


@login_required
def modificar_cita(request, id):
    """
    Permite al usuario modificar su cita cambiando el horario.
    Usa transacciones atómicas para evitar condiciones de carrera.
    """
    from datetime import date
    from django.db import transaction
    
    # Obtener el horario reservado actual
    horario_agenda_actual = get_object_or_404(
        HorarioAgenda.objects.select_related('agenda', 'agenda__psicologo', 'horario', 'reservado_por'),
        pk=id
    )
    
    # Verificar que el usuario esté autenticado y tenga un perfil Persona
    try:
        persona = request.user.persona
    except Persona.DoesNotExist:
        messages.error(request, "Tu perfil de usuario no está completo.")
        return redirect('form_persona')
    
    # Verificar que el horario pertenezca al usuario
    if horario_agenda_actual.reservado_por != persona:
        messages.error(request, "No tienes permiso para modificar esta cita.")
        return redirect('autenticar_persona')
    
    # Verificar que la cita no sea del pasado (usando función centralizada)
    from .helpers import validar_cita_puede_modificarse
    try:
        validar_cita_puede_modificarse(horario_agenda_actual)
    except ValidationError as e:
        messages.warning(request, str(e))
        return redirect('autenticar_persona')
    
    agenda = horario_agenda_actual.agenda
    
    # Verificar que la agenda no sea del pasado
    if agenda.data < date.today():
        messages.error(request, "No puedes modificar una cita en una fecha que ya pasó.")
        return redirect('autenticar_persona')
    
    if request.method == 'POST':
        # Obtener el nuevo horario desde el POST
        nuevo_horario_id = request.POST.get('nuevo_horario_id')
        
        if not nuevo_horario_id:
            messages.error(request, "Debes seleccionar un nuevo horario.")
            return redirect('modificar_cita', id=id)
        
        # Verificar que no sea el mismo horario
        if int(nuevo_horario_id) == horario_agenda_actual.id:
            messages.warning(request, "Ya tienes reservado este horario.")
            return redirect('modificar_cita', id=id)
        
        try:
            with transaction.atomic():
                # Buscar el nuevo horario disponible y bloquearlo
                nuevo_horario_agenda = HorarioAgenda.objects.select_for_update().get(
                    agenda=agenda,
                    id=nuevo_horario_id,
                    reservado_por__isnull=True  # Solo si está disponible
                )
                
                # Liberar el horario actual
                horario_agenda_actual.reservado_por = None
                horario_agenda_actual.save()
                
                # Reservar el nuevo horario
                nuevo_horario_agenda.reservado_por = persona
                nuevo_horario_agenda.save()
                
                logger.info(
                    f"Cita modificada: Usuario {persona.rut} cambió de horario "
                    f"{horario_agenda_actual.horario.horas} a {nuevo_horario_agenda.horario.horas} "
                    f"en agenda {agenda.id}"
                )
            
            messages.success(
                request,
                f"¡Cita modificada exitosamente! Tu horario ha sido cambiado a {nuevo_horario_agenda.horario.horas}."
            )
            
            return redirect('autenticar_persona')
            
        except HorarioAgenda.DoesNotExist:
            messages.error(request, "El horario seleccionado no está disponible.")
            return redirect('modificar_cita', id=id)
        except Exception as e:
            logger.error(f"Error al modificar cita: {e}", exc_info=True)
            messages.error(request, "Ocurrió un error al modificar la cita. Por favor, intenta nuevamente.")
            return redirect('modificar_cita', id=id)
    
    # GET: Mostrar formulario de modificación
    # Obtener horarios disponibles en la misma agenda
    horarios_disponibles = agenda.get_horarios_disponibles().select_related('horario')
    
    context = {
        'horario_agenda_actual': horario_agenda_actual,
        'agenda': agenda,
        'persona': persona,
        'horarios_disponibles': horarios_disponibles,
    }
    
    return render(request, 'core/modificar_cita.html', context)


@rate_limit(max_attempts=5, window=300, key_prefix='auth_ip')
@rate_limit_by_username(max_attempts=5, window=300, key_prefix='auth_user')
def autenticar_persona(request):
    """
    Autentica a un usuario y lo redirige a su área personal.
    Si ya está autenticado, muestra su área directamente.
    Incluye rate limiting para proteger contra ataques de fuerza bruta.
    """
    if request.user.is_authenticated:
        # El usuario ya está autenticado, redirige a la página deseada
        try:
            persona = request.user.persona
            # Obtener todas las reservas con sus horarios
            reservas_query = HorarioAgenda.objects.filter(
                reservado_por=persona
            ).select_related('agenda', 'agenda__psicologo', 'agenda__psicologo__especialidad', 'horario').order_by('agenda__data', 'horario__horas')
            
            # Paginación: 5 citas por página
            paginator = Paginator(reservas_query, 5)
            page = request.GET.get('page', 1)
            
            try:
                reservas = paginator.page(page)
            except PageNotAnInteger:
                reservas = paginator.page(1)
            except EmptyPage:
                reservas = paginator.page(paginator.num_pages)
            
            return render(request, 'core/area_de_persona.html', {
                'persona': persona,
                'reservas': reservas,
                'paginator': paginator,
                'page_obj': reservas
            })
        except Persona.DoesNotExist:
            messages.error(request, "Tu perfil de usuario no está completo. Por favor, completa tu perfil.")
            return redirect('form_persona')
    else:
        # Si no está autenticado, verifica las credenciales y realiza la autenticación
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if not username or not password:
                messages.error(request, "Por favor, completa todos los campos.")
                request.login_failed = True
                return render(request, 'core/coming_son.html', {})
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    logger.info(f"Login exitoso para usuario: {username}")
                    try:
                        persona = user.persona
                        # Obtener todas las reservas con sus horarios
                        reservas_query = HorarioAgenda.objects.filter(
                            reservado_por=persona
                        ).select_related('agenda', 'agenda__psicologo', 'agenda__psicologo__especialidad', 'horario').order_by('agenda__data', 'horario__horas')
                        
                        # Paginación: 5 citas por página
                        paginator = Paginator(reservas_query, 5)
                        page = request.GET.get('page', 1)
                        
                        try:
                            reservas = paginator.page(page)
                        except PageNotAnInteger:
                            reservas = paginator.page(1)
                        except EmptyPage:
                            reservas = paginator.page(paginator.num_pages)
                        
                        return render(request, 'core/area_de_persona.html', {
                            'persona': persona,
                            'reservas': reservas,
                            'paginator': paginator,
                            'page_obj': reservas
                        })
                    except Persona.DoesNotExist:
                        messages.error(request, "Tu perfil de usuario no está completo. Por favor, completa tu perfil.")
                        return redirect('form_persona')
                else:
                    # Usuario inactivo
                    messages.error(request, "Usuario Inactivo")
                    request.login_failed = True
                    logger.warning(f"Intento de login con usuario inactivo: {username}")
                    return render(request, 'core/coming_son.html', {})
            else:
                messages.error(request, "Usuario y/o contraseña incorrectos.")
                request.login_failed = True
                logger.warning(f"Intento de login fallido para usuario: {username}")
                return render(request, 'core/coming_son.html', {})
        else:
            # Si es GET, redirige al login o a coming_son
            return render(request, 'core/coming_son.html', {})





