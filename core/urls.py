"""
URLs de la aplicación core.
"""
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import reserva
from . import views

# Importaciones organizadas
from .views import (
    form_persona, form_borrar_persona, eliminar_cuenta_usuario,
    form_mod_persona, form_post, form_mod_post, form_borrar_post,
    registrar_usuario, index, nos, coming_son, log, login_view,
    logout_view, lista_usuarios, forgetpassword, changepassword,
    frontpage, post_detail, editar_comentario, changepassword_login,
    detectar_sentimiento, marcar_notificacion_superusuario, comprobante_registro
)
from .reserva import adm, comprobante_reserva, descargar_comprobante_pdf, cancelar_cita, modificar_cita
from . import videocall
from . import views_chatbot, views_grupos

urlpatterns = [
    # Páginas principales
    path('', index, name='index'),
    path('nos/', nos, name='nos'),
    path('coming_son/', coming_son, name='coming_son'),
    
    # Autenticación
    path('log/', log, name='log'),
    path('login/', LoginView.as_view(template_name='core/log.html'), name="login"),
    path('sesion/', login_view, name="sesion"),
    path('logout/', logout_view, name="logout"),
    
    # Registro y gestión de usuarios
    path('registrar_usuario/', registrar_usuario, name="registrar_usuario"),
    path('comprobante_registro/<str:rut>/', comprobante_registro, name='comprobante_registro'),
    path('lista_usuarios/', lista_usuarios, name='lista_usuarios'), 
    # Gestión de perfiles
    path('form_persona/', form_persona, name='form_persona'),
    path('form_mod_persona/', form_mod_persona, name='form_mod_persona'),
    path('form_borrar_persona/<str:id>/', form_borrar_persona, name='form_borrar_persona'),
    path('eliminar_cuenta_usuario/', eliminar_cuenta_usuario, name='eliminar_cuenta_usuario'),
    
    # Recuperación de contraseña
    path('forgetpassword/', forgetpassword, name="forgetpassword"),
    path('changepassword/<token>/', changepassword, name='changepassword'),
    path('changepassword/', changepassword_login, name="changepassword_login"),
    
    # Posts y comentarios
    path('frontpage/', views.frontpage, name='frontpage'),
    path('form_post/', views.form_post, name='form_post'),
    path('form_mod_post/<int:post_id>/', views.form_mod_post, name='form_mod_post'),
    path('form_borrar_post/<int:id>/', views.form_borrar_post, name='form_borrar_post'),
    
    # Sistema de moderación y reportes
    path('reportar_post/<int:post_id>/', views.reportar_post, name='reportar_post'),
    path('reportar_comentario/<int:comment_id>/', views.reportar_comentario, name='reportar_comentario'),
    path('moderacion/', views.panel_moderacion, name='panel_moderacion'),
    path('moderar_post/<int:post_id>/<str:accion>/', views.moderar_post, name='moderar_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('editar_comentario/<int:comment_id>/', views.editar_comentario, name='editar_comentario'),
    
    # Notificaciones
    path('mostrar_notificaciones/', views.mostrar_notificaciones, name='mostrar_notificaciones'),
    path('marcar-notificacion-superusuario-leida/<int:notificacion_id>/', 
         marcar_notificacion_superusuario, name='marcar_notificacion_superusuario_leida'),
    path('marcar-notificacion-leida/<int:notificacion_id>/', 
         views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('eliminar-notificacion/<int:notificacion_id>/', 
         views.eliminar_notificacion, name='eliminar_notificacion'),
    
    # Análisis de sentimientos
    path('detectar_sentimiento/', detectar_sentimiento, name='detectar_sentimiento'),
    
    # Reservas y psicólogos (ANTES de la ruta genérica de slug)
    path('psicologo/new/', reserva.registrar_psicologo, name='registrar_psicologo'), 
    path('especialidad/new/', reserva.registrar_especialidad, name='registrar_especialidad'),
    path('horarios/new/', reserva.insertar_horarios, name='insertar_horarios'),
    path('agenda/new/', reserva.crear_nueva_agenda, name='crear_nueva_agenda'),
    path('listar_agendas/', reserva.listar_agendas, name='listar_agendas'),
    path('detallar_agenda/<int:id>/', reserva.detallar_agenda, name='detallar_agenda'),
    path('adm/', adm, name='adm'),
    path('autenticar_persona/', reserva.autenticar_persona, name='autenticar_persona'),
    path('area_de_persona/<int:id>/', reserva.area_de_persona, name='area_de_persona'),
    path('marcar_consulta/<int:id>/', reserva.marcar_consulta, name='marcar_consulta'),
    path('comprobante_reserva/<int:id>/', comprobante_reserva, name='comprobante_reserva'),
    path('descargar_comprobante_pdf/<int:id>/', descargar_comprobante_pdf, name='descargar_comprobante_pdf'),
    path('cancelar_cita/<int:id>/', cancelar_cita, name='cancelar_cita'),
    path('modificar_cita/<int:id>/', modificar_cita, name='modificar_cita'),
    
    # Videollamadas y Chat
    path('videocall/lobby/', videocall.videocall_lobby, name='videocall_lobby'),
    path('videocall/room/<str:room_name>/', videocall.videocall_room, name='videocall_room'),
    path('videocall/get_token/', videocall.get_agora_token, name='get_agora_token'),
    path('videocall/create_room/', videocall.create_room, name='create_room'),
    path('videocall/create_member/', videocall.create_room_member, name='create_room_member'),
    path('videocall/get_member/', videocall.get_room_member, name='get_room_member'),
    path('videocall/delete_member/', videocall.delete_room_member, name='delete_room_member'),
    path('videocall/send_message/', videocall.send_chat_message, name='send_chat_message'),
    path('videocall/get_messages/<str:room_name>/', videocall.get_chat_messages, name='get_chat_messages'),
    path('videocall/set_typing/', videocall.set_typing_status, name='set_typing_status'),
    path('videocall/get_typing/<str:room_name>/', videocall.get_typing_status, name='get_typing_status'),
    path('videocall/get_participants/<str:room_name>/', videocall.get_room_participants, name='get_room_participants'),
    path('videocall/kick_participant/', videocall.kick_participant, name='kick_participant'),
    path('videocall/crear_sala/<int:horario_agenda_id>/', videocall.crear_sala_desde_cita, name='crear_sala_desde_cita'),
    
    # Chatbot con OpenAI
    path('chatbot/', views_chatbot.chatbot_view, name='chatbot'),
    path('chatbot/<int:conversacion_id>/', views_chatbot.chatbot_view, name='chatbot_conversation'),
    path('chatbot/send/', views_chatbot.chatbot_send_message, name='chatbot_send_message'),
    path('chatbot/history/<int:conversacion_id>/', views_chatbot.chatbot_get_history, name='chatbot_get_history'),
    path('chatbot/new/', views_chatbot.chatbot_new_conversation, name='chatbot_new_conversation'),
    path('chatbot/list/', views_chatbot.chatbot_list_conversations, name='chatbot_list_conversations'),
    path('chatbot/delete/<int:conversacion_id>/', views_chatbot.chatbot_delete_conversation, name='chatbot_delete_conversation'),
    path('chatbot/delete-multiple/', views_chatbot.chatbot_delete_multiple, name='chatbot_delete_multiple'),
    
    # Grupos de Apoyo
    path('grupos/', views_grupos.listar_grupos, name='listar_grupos'),
    path('grupos/crear/', views_grupos.crear_grupo, name='crear_grupo'),
    path('grupos/<int:grupo_id>/', views_grupos.detalle_grupo, name='detalle_grupo'),
    path('grupos/<int:grupo_id>/unirse/', views_grupos.unirse_grupo_view, name='unirse_grupo'),
    path('grupos/<int:grupo_id>/salir/', views_grupos.salir_grupo_view, name='salir_grupo'),
    path('grupos/<int:grupo_id>/sala/', views_grupos.sala_grupo, name='sala_grupo'),
    
    # Ruta genérica de posts (DEBE IR AL FINAL para no capturar otras rutas)
    path('<slug:slug>/', views.post_detail, name='post_detail'),
]


