"""
WebSocket consumers para tiempo real de pizarra colaborativa
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatMessage, VideoCallRoom, Persona
from django.utils import timezone


class WhiteboardConsumer(AsyncWebsocketConsumer):
    """
    Consumer para mensajes de pizarra en tiempo real
    """
    
    async def connect(self):
        """Conectar al WebSocket"""
        # Obtener room_name de la URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'whiteboard_{self.room_name}'
        
        # Verificar autenticación
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        # Unirse al grupo de la sala
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Desconectar del WebSocket"""
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recibir mensaje del WebSocket"""
        try:
            data = json.loads(text_data)
            action_type = data.get('type')
            
            if action_type == 'whiteboard_action':
                action = data.get('action')
                
                # LOG ESPECÍFICO PARA BORRADO (incluyendo borrado de post-its)
                if action and (action.get('tool') == 'eraser' or action.get('type') == 'clear' or action.get('type') == 'postit_delete'):
                    import logging
                    logger = logging.getLogger('whiteboard')
                    logger.info(f"[WebSocket] 🧹 RECIBIENDO ACCIÓN DE BORRADO: action_id={action.get('id')}, tool={action.get('tool')}, type={action.get('type')}, user={self.scope['user'].username}, room={data.get('room_name')}")
                
                # Guardar mensaje en BD
                await self.save_message(action, data.get('room_name'), self.scope['user'])
                
                # Enviar a todos en el grupo
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'whiteboard_action',
                        'action': action,
                        'user_id': str(self.scope['user'].id) if hasattr(self.scope['user'], 'id') else None,
                        'username': self.scope['user'].username if hasattr(self.scope['user'], 'username') else 'Usuario',
                    }
                )
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error en receive: {e}")
    
    async def whiteboard_action(self, event):
        """Enviar acción de pizarra al WebSocket"""
        # Enviar solo si no es del mismo usuario (evitar eco)
        current_user_id = str(self.scope['user'].id) if hasattr(self.scope['user'], 'id') and not self.scope['user'].is_anonymous else None
        event_user_id = event.get('user_id')
        
        # LOG ESPECÍFICO PARA BORRADO (incluyendo borrado de post-its)
        action = event.get('action')
        if action and (action.get('tool') == 'eraser' or action.get('type') == 'clear' or action.get('type') == 'postit_delete'):
            import logging
            logger = logging.getLogger('whiteboard')
            logger.info(f"[WebSocket] 🧹 ENVIANDO ACCIÓN DE BORRADO: action_id={action.get('id')}, from_user={event.get('username')}, to_user={self.scope['user'].username if not self.scope['user'].is_anonymous else 'anonymous'}, will_send={event_user_id != current_user_id if event_user_id and current_user_id else 'unknown'}")
        
        if event_user_id and current_user_id and event_user_id != current_user_id:
            await self.send(text_data=json.dumps({
                'type': 'whiteboard_action',
                'action': event['action'],
                'user_id': event['user_id'],
                'username': event['username'],
            }))
    
    @database_sync_to_async
    def save_message(self, action, room_name, user):
        """Guardar mensaje en la base de datos"""
        try:
            # Obtener la sala (debe existir)
            try:
                room = VideoCallRoom.objects.get(name=room_name, is_active=True)
            except VideoCallRoom.DoesNotExist:
                print(f"Error: Sala {room_name} no encontrada")
                return
            
            # Obtener Persona del usuario
            try:
                persona = Persona.objects.get(user=user)
            except Persona.DoesNotExist:
                print(f"Error: Persona no encontrada para usuario {user.username}")
                return
            
            # Crear mensaje
            message_text = f'WHITEBOARD:{json.dumps(action)}'
            ChatMessage.objects.create(
                room=room,
                author=persona,
                message=message_text
            )
        except Exception as e:
            print(f"Error guardando mensaje: {e}")

