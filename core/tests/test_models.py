"""
Tests unitarios para los modelos de ZenMindConnect.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from core.models import (
    Persona, Tipousuario, Post, Comment, Psicologo, Especialidad,
    Horarios, Agenda, HorarioAgenda, Hilo, Notificacion
)
from datetime import date, timedelta


class TipousuarioModelTest(TestCase):
    """Tests para el modelo Tipousuario."""
    
    def setUp(self):
        self.tipo_admin = Tipousuario.objects.create(tipoUsuario='Administrador')
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
    
    def test_tipousuario_creation(self):
        """Test que se puede crear un Tipousuario."""
        self.assertEqual(self.tipo_admin.tipoUsuario, 'Administrador')
        self.assertEqual(self.tipo_regular.tipoUsuario, 'Regular')
    
    def test_tipousuario_str(self):
        """Test el método __str__ de Tipousuario."""
        self.assertEqual(str(self.tipo_admin), 'Administrador')
    
    def test_tipousuario_constants(self):
        """Test que las constantes están definidas."""
        self.assertEqual(Tipousuario.TIPO_ADMIN, 1)
        self.assertEqual(Tipousuario.TIPO_REGULAR, 2)


class PersonaModelTest(TestCase):
    """Tests para el modelo Persona."""
    
    def setUp(self):
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_persona_creation(self):
        """Test que se puede crear una Persona."""
        persona = Persona.objects.create(
            rut='12345678-9',
            nombre='Juan',
            apellido='Pérez',
            fechaNac=date(1990, 1, 1),
            correo='juan@example.com',
            telefono='+56912345678',
            contrasena='password123',
            tipousuario=self.tipo_regular,
            user=self.user
        )
        self.assertEqual(persona.rut, '12345678-9')
        self.assertEqual(persona.nombre, 'Juan')
        self.assertEqual(persona.user, self.user)
    
    def test_persona_unique_email(self):
        """Test que el email debe ser único."""
        Persona.objects.create(
            rut='12345678-9',
            nombre='Juan',
            apellido='Pérez',
            fechaNac=date(1990, 1, 1),
            correo='juan@example.com',
            telefono='+56912345678',
            contrasena='password123',
            tipousuario=self.tipo_regular,
            user=self.user
        )
        
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Persona.objects.create(
                rut='98765432-1',
                nombre='Pedro',
                apellido='González',
                fechaNac=date(1990, 1, 1),
                correo='juan@example.com',  # Email duplicado
                telefono='+56987654321',
                contrasena='password123',
                tipousuario=self.tipo_regular,
                user=user2
            )


class PostModelTest(TestCase):
    """Tests para el modelo Post."""
    
    def setUp(self):
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.persona = Persona.objects.create(
            rut='12345678-9',
            nombre='Juan',
            apellido='Pérez',
            fechaNac=date(1990, 1, 1),
            correo='juan@example.com',
            telefono='+56912345678',
            contrasena='password123',
            tipousuario=self.tipo_regular,
            user=self.user
        )
        self.hilo = Hilo.objects.create(nombreHilo='Salud Mental')
    
    def test_post_creation(self):
        """Test que se puede crear un Post."""
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            intro='Introducción del post',
            body='Cuerpo del post',
            hilo=self.hilo,
            author=self.persona
        )
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.persona)
        self.assertEqual(post.slug, 'test-post')
    
    def test_post_slug_generation(self):
        """Test que el slug se genera automáticamente."""
        post = Post(
            title='Test Post Title',
            intro='Introducción',
            body='Cuerpo',
            hilo=self.hilo,
            author=self.persona
        )
        post.save()
        self.assertTrue(post.slug.startswith('test-post-title'))


class CommentModelTest(TestCase):
    """Tests para el modelo Comment."""
    
    def setUp(self):
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.persona = Persona.objects.create(
            rut='12345678-9',
            nombre='Juan',
            apellido='Pérez',
            fechaNac=date(1990, 1, 1),
            correo='juan@example.com',
            telefono='+56912345678',
            contrasena='password123',
            tipousuario=self.tipo_regular,
            user=self.user
        )
        self.hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            intro='Introducción',
            body='Cuerpo',
            hilo=self.hilo,
            author=self.persona
        )
    
    def test_comment_creation(self):
        """Test que se puede crear un Comment."""
        comment = Comment.objects.create(
            post=self.post,
            name='Comentador',
            body='Este es un comentario de prueba',
            author=self.persona
        )
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.body, 'Este es un comentario de prueba')
        self.assertEqual(comment.author, self.persona)


class AgendaModelTest(TestCase):
    """Tests para el modelo Agenda."""
    
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Psicología Clínica')
        self.psicologo = Psicologo.objects.create(
            nombre='Dr. Test',
            rut='11111111-1',
            email='test@example.com',
            telefono='+56912345678',
            especialidad=self.especialidad
        )
        self.horario = Horarios.objects.create(horas='08:00AM⛅')
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.persona = Persona.objects.create(
            rut='12345678-9',
            nombre='Test',
            apellido='User',
            fechaNac=date(1990, 1, 1),
            correo='test@example.com',
            telefono='+56912345678',
            contrasena='testpass123',
            tipousuario=self.tipo_regular,
            user=self.user
        )
    
    def test_agenda_creation(self):
        """Test que se puede crear una Agenda."""
        agenda = Agenda.objects.create(
            psicologo=self.psicologo,
            data=date.today() + timedelta(days=7)
        )
        self.assertEqual(agenda.psicologo, self.psicologo)
        self.assertIsNotNone(agenda.data)
    
    def test_agenda_get_horarios_disponibles(self):
        """Test el método get_horarios_disponibles."""
        agenda = Agenda.objects.create(
            psicologo=self.psicologo,
            data=date.today() + timedelta(days=7)
        )
        HorarioAgenda.objects.create(
            agenda=agenda,
            horario=self.horario
        )
        disponibles = agenda.get_horarios_disponibles()
        self.assertEqual(disponibles.count(), 1)
    
    def test_agenda_get_horarios_reservados(self):
        """Test el método get_horarios_reservados."""
        agenda = Agenda.objects.create(
            psicologo=self.psicologo,
            data=date.today() + timedelta(days=7)
        )
        horario_agenda = HorarioAgenda.objects.create(
            agenda=agenda,
            horario=self.horario,
            reservado_por=self.persona
        )
        reservados = agenda.get_horarios_reservados()
        self.assertEqual(reservados.count(), 1)
        self.assertEqual(reservados.first(), horario_agenda)
    
    def test_agenda_str(self):
        """Test el método __str__ de Agenda."""
        agenda = Agenda.objects.create(
            psicologo=self.psicologo,
            data=date.today() + timedelta(days=7)
        )
        self.assertEqual(str(agenda), self.psicologo.nombre)


class HorarioAgendaModelTest(TestCase):
    """Tests para el modelo HorarioAgenda."""
    
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Psicología Clínica')
        self.psicologo = Psicologo.objects.create(
            nombre='Dr. Test',
            rut='11111111-1',
            email='test@example.com',
            telefono='+56912345678',
            especialidad=self.especialidad
        )
        self.horario = Horarios.objects.create(horas='08:00AM⛅')
        self.agenda = Agenda.objects.create(
            psicologo=self.psicologo,
            data=date.today() + timedelta(days=7)
        )
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.persona = Persona.objects.create(
            rut='12345678-9',
            nombre='Test',
            apellido='User',
            fechaNac=date(1990, 1, 1),
            correo='test@example.com',
            telefono='+56912345678',
            contrasena='testpass123',
            tipousuario=self.tipo_regular,
            user=self.user
        )
    
    def test_horario_agenda_creation(self):
        """Test que se puede crear un HorarioAgenda."""
        horario_agenda = HorarioAgenda.objects.create(
            agenda=self.agenda,
            horario=self.horario
        )
        self.assertEqual(horario_agenda.agenda, self.agenda)
        self.assertEqual(horario_agenda.horario, self.horario)
        self.assertIsNone(horario_agenda.reservado_por)
    
    def test_horario_agenda_reservado(self):
        """Test que se puede reservar un horario."""
        horario_agenda = HorarioAgenda.objects.create(
            agenda=self.agenda,
            horario=self.horario,
            reservado_por=self.persona
        )
        self.assertEqual(horario_agenda.reservado_por, self.persona)
        self.assertFalse(horario_agenda.esta_disponible)
    
    def test_horario_agenda_esta_disponible(self):
        """Test la propiedad esta_disponible."""
        horario_agenda = HorarioAgenda.objects.create(
            agenda=self.agenda,
            horario=self.horario
        )
        self.assertTrue(horario_agenda.esta_disponible)
        
        horario_agenda.reservado_por = self.persona
        horario_agenda.save()
        self.assertFalse(horario_agenda.esta_disponible)
    
    def test_horario_agenda_unique_together(self):
        """Test que no se puede crear dos HorarioAgenda con mismo agenda y horario."""
        HorarioAgenda.objects.create(
            agenda=self.agenda,
            horario=self.horario
        )
        with self.assertRaises(Exception):  # IntegrityError
            HorarioAgenda.objects.create(
                agenda=self.agenda,
                horario=self.horario
            )
    
    def test_horario_agenda_str(self):
        """Test el método __str__ de HorarioAgenda."""
        horario_agenda = HorarioAgenda.objects.create(
            agenda=self.agenda,
            horario=self.horario
        )
        self.assertIn('Disponible', str(horario_agenda))
        
        horario_agenda.reservado_por = self.persona
        horario_agenda.save()
        self.assertIn('Reservado', str(horario_agenda))


class PsicologoModelTest(TestCase):
    """Tests para el modelo Psicologo."""
    
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Psicología Clínica')
    
    def test_psicologo_creation(self):
        """Test que se puede crear un Psicologo."""
        psicologo = Psicologo.objects.create(
            nombre='Dr. Test',
            rut='11111111-1',
            email='test@example.com',
            telefono='+56912345678',
            especialidad=self.especialidad
        )
        self.assertEqual(psicologo.nombre, 'Dr. Test')
        self.assertEqual(psicologo.especialidad, self.especialidad)
    
    def test_psicologo_rut_unique(self):
        """Test que el RUT debe ser único."""
        Psicologo.objects.create(
            nombre='Dr. Test',
            rut='11111111-1',
            email='test@example.com',
            telefono='+56912345678',
            especialidad=self.especialidad
        )
        with self.assertRaises(Exception):  # IntegrityError
            Psicologo.objects.create(
                nombre='Dr. Test 2',
                rut='11111111-1',  # RUT duplicado
                email='test2@example.com',
                telefono='+56987654321',
                especialidad=self.especialidad
            )
    
    def test_psicologo_str(self):
        """Test el método __str__ de Psicologo."""
        psicologo = Psicologo.objects.create(
            nombre='Dr. Test',
            rut='11111111-1',
            email='test@example.com',
            telefono='+56912345678',
            especialidad=self.especialidad
        )
        self.assertEqual(str(psicologo), 'Dr. Test')


class EspecialidadModelTest(TestCase):
    """Tests para el modelo Especialidad."""
    
    def test_especialidad_creation(self):
        """Test que se puede crear una Especialidad."""
        especialidad = Especialidad.objects.create(nombre='Psicología Clínica')
        self.assertEqual(especialidad.nombre, 'Psicología Clínica')
    
    def test_especialidad_str(self):
        """Test el método __str__ de Especialidad."""
        especialidad = Especialidad.objects.create(nombre='Psicología Clínica')
        self.assertEqual(str(especialidad), 'Psicología Clínica')


class HiloModelTest(TestCase):
    """Tests para el modelo Hilo."""
    
    def test_hilo_creation(self):
        """Test que se puede crear un Hilo."""
        hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.assertEqual(hilo.nombreHilo, 'Salud Mental')
    
    def test_hilo_str(self):
        """Test el método __str__ de Hilo."""
        hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.assertEqual(str(hilo), 'Salud Mental')


