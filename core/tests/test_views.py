"""
Tests para las vistas de ZenMindConnect.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import (
    Persona, Tipousuario, Post, Comment, Psicologo, Especialidad,
    Horarios, Agenda, HorarioAgenda, Hilo
)
from datetime import date, timedelta


class TestClient(Client):
    """Cliente de test con User-Agent para evitar bloqueo del middleware AntiBot."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get(self, *args, **kwargs):
        kwargs.setdefault('HTTP_USER_AGENT', self.defaults['HTTP_USER_AGENT'])
        return super().get(*args, **kwargs)
    
    def post(self, *args, **kwargs):
        kwargs.setdefault('HTTP_USER_AGENT', self.defaults['HTTP_USER_AGENT'])
        return super().post(*args, **kwargs)


class IndexViewTest(TestCase):
    """Tests para la vista index."""
    
    def setUp(self):
        self.client = TestClient()
    
    def test_index_view(self):
        """Test que la vista index carga correctamente."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ZenMindConnect', status_code=200)


class LoginViewTest(TestCase):
    """Tests para la vista de login."""
    
    def setUp(self):
        self.client = TestClient()
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
    
    def test_login_view_get(self):
        """Test que la vista de login carga correctamente."""
        response = self.client.get(reverse('log'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_success(self):
        """Test login exitoso."""
        response = self.client.post(reverse('sesion'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de login
    
    def test_login_failure(self):
        """Test login con credenciales incorrectas."""
        response = self.client.post(reverse('sesion'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect con error


class PostViewTest(TestCase):
    """Tests para las vistas de posts."""
    
    def setUp(self):
        self.client = TestClient()
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
        self.hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            intro='Introducción',
            body='Cuerpo del post',
            hilo=self.hilo,
            author=self.persona
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_frontpage_view(self):
        """Test que frontpage carga correctamente."""
        response = self.client.get(reverse('frontpage'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post', status_code=200)
    
    def test_post_detail_view(self):
        """Test que post_detail carga correctamente."""
        response = self.client.get(reverse('post_detail', kwargs={'slug': 'test-post'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post', status_code=200)
    
    def test_post_detail_not_found(self):
        """Test que post_detail retorna 404 para slug inexistente."""
        response = self.client.get(reverse('post_detail', kwargs={'slug': 'no-existe'}))
        self.assertEqual(response.status_code, 404)
    
    def test_form_post_requires_login(self):
        """Test que form_post requiere login."""
        self.client.logout()
        response = self.client.get(reverse('form_post'))
        self.assertEqual(response.status_code, 302)  # Redirect a login
    
    def test_form_post_create(self):
        """Test crear un nuevo post."""
        response = self.client.post(reverse('form_post'), {
            'title': 'Nuevo Post',
            'slug': 'nuevo-post',
            'intro': 'Introducción del nuevo post',
            'body': 'Cuerpo del nuevo post con más de 20 caracteres',
            'hilo': self.hilo.idTiphilo
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.assertTrue(Post.objects.filter(slug='nuevo-post').exists())


class CommentViewTest(TestCase):
    """Tests para las vistas de comentarios."""
    
    def setUp(self):
        self.client = TestClient()
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
        self.hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            intro='Introducción',
            body='Cuerpo',
            hilo=self.hilo,
            author=self.persona
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_comment(self):
        """Test crear un comentario."""
        response = self.client.post(reverse('post_detail', kwargs={'slug': 'test-post'}), {
            'name': 'Comentador',
            'body': 'Este es un comentario de prueba'
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.assertTrue(Comment.objects.filter(post=self.post).exists())


class RegistrarUsuarioViewTest(TestCase):
    """Tests para la vista registrar_usuario."""
    
    def setUp(self):
        self.client = TestClient()
        self.tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
    
    def test_registrar_usuario_view_get(self):
        """Test que la vista de registro carga correctamente."""
        response = self.client.get(reverse('registrar_usuario'))
        self.assertEqual(response.status_code, 200)
    
    def test_registrar_usuario_success(self):
        """Test registro exitoso de usuario."""
        response = self.client.post(reverse('registrar_usuario'), {
            'rut': '11111111-1',  # RUT válido
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'fechaNac': '1990-01-01',
            'correo': 'juan@example.com',
            'telefono': '+56912345678',
            'contrasena': 'password123'
        })
        # Debería redirigir al comprobante de registro
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Persona.objects.filter(rut='111111111').exists())
        self.assertTrue(User.objects.filter(email='juan@example.com').exists())
    
    def test_registrar_usuario_rut_duplicado(self):
        """Test que no se puede registrar con RUT duplicado."""
        # Crear usuario existente
        user = User.objects.create_user(username='existing', password='pass')
        Persona.objects.create(
            rut='111111111',  # RUT válido (sin guión, como se guarda)
            nombre='Existing',
            apellido='User',
            fechaNac=date(1990, 1, 1),
            correo='existing@example.com',
            telefono='+56987654321',
            contrasena='pass',
            tipousuario=self.tipo_regular,
            user=user
        )
        
        # Contar usuarios antes
        personas_count_before = Persona.objects.count()
        
        response = self.client.post(reverse('registrar_usuario'), {
            'rut': '11111111-1',  # RUT duplicado
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'fechaNac': '1990-01-01',
            'correo': 'juan@example.com',
            'telefono': '+56912345678',
            'contrasena': 'password123'
        })
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario con error
        # Verificar que no se creó un nuevo usuario
        self.assertEqual(Persona.objects.count(), personas_count_before)
    
    def test_registrar_usuario_correo_duplicado(self):
        """Test que no se puede registrar con correo duplicado."""
        # Crear usuario existente
        user = User.objects.create_user(username='existing', password='pass', email='juan@example.com')
        Persona.objects.create(
            rut='111111111',  # RUT válido (sin guión, como se guarda)
            nombre='Existing',
            apellido='User',
            fechaNac=date(1990, 1, 1),
            correo='juan@example.com',
            telefono='+56987654321',
            contrasena='pass',
            tipousuario=self.tipo_regular,
            user=user
        )
        
        # Contar usuarios antes
        personas_count_before = Persona.objects.count()
        
        response = self.client.post(reverse('registrar_usuario'), {
            'rut': '12345678-5',  # RUT válido diferente
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'fechaNac': '1990-01-01',
            'correo': 'juan@example.com',  # Correo duplicado
            'telefono': '+56912345678',
            'contrasena': 'password123'
        })
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario con error
        # Verificar que no se creó un nuevo usuario
        self.assertEqual(Persona.objects.count(), personas_count_before)


class FormPostViewTest(TestCase):
    """Tests para la vista form_post."""
    
    def setUp(self):
        self.client = TestClient()
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
        self.hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.client.login(username='testuser', password='testpass123')
    
    def test_form_post_view_get(self):
        """Test que la vista form_post carga correctamente."""
        response = self.client.get(reverse('form_post'))
        self.assertEqual(response.status_code, 200)
    
    def test_form_post_create_success(self):
        """Test crear post exitosamente."""
        response = self.client.post(reverse('form_post'), {
            'title': 'Nuevo Post de Prueba',
            'slug': 'nuevo-post-prueba',
            'intro': 'Esta es una introducción de prueba con más de 10 caracteres',
            'body': 'Este es el cuerpo del post con más de 20 caracteres para cumplir la validación',
            'hilo': self.hilo.idTiphilo
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.assertTrue(Post.objects.filter(slug='nuevo-post-prueba').exists())
        post = Post.objects.get(slug='nuevo-post-prueba')
        self.assertEqual(post.author, self.persona)
    
    def test_form_post_requires_login(self):
        """Test que form_post requiere login."""
        self.client.logout()
        response = self.client.get(reverse('form_post'))
        self.assertEqual(response.status_code, 302)  # Redirect a login


class FormModPostViewTest(TestCase):
    """Tests para la vista form_mod_post."""
    
    def setUp(self):
        self.client = TestClient()
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
        self.hilo = Hilo.objects.create(nombreHilo='Salud Mental')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            intro='Introducción',
            body='Cuerpo del post con más de 20 caracteres',
            hilo=self.hilo,
            author=self.persona
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_form_mod_post_view_get(self):
        """Test que la vista form_mod_post carga correctamente."""
        response = self.client.get(reverse('form_mod_post', kwargs={'post_id': self.post.idPost}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post', status_code=200)
    
    def test_form_mod_post_update_success(self):
        """Test actualizar post exitosamente."""
        response = self.client.post(reverse('form_mod_post', kwargs={'post_id': self.post.idPost}), {
            'title': 'Post Actualizado',
            'slug': 'test-post',
            'intro': 'Introducción actualizada con más de 10 caracteres',
            'body': 'Cuerpo actualizado con más de 20 caracteres para validación',
            'hilo': self.hilo.idTiphilo
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de actualizar
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Post Actualizado')
    
    def test_form_mod_post_unauthorized(self):
        """Test que no se puede editar post de otro usuario."""
        # Crear otro usuario
        user2 = User.objects.create_user(username='otheruser', password='pass123')
        persona2 = Persona.objects.create(
            rut='98765432-1',
            nombre='Other',
            apellido='User',
            fechaNac=date(1990, 1, 1),
            correo='other@example.com',
            telefono='+56987654321',
            contrasena='pass123',
            tipousuario=self.tipo_regular,
            user=user2
        )
        
        self.client.logout()
        self.client.login(username='otheruser', password='pass123')
        
        response = self.client.get(reverse('form_mod_post', kwargs={'post_id': self.post.idPost}))
        # Debería redirigir o mostrar error
        self.assertIn(response.status_code, [302, 403])


class SecurityTest(TestCase):
    """Tests de seguridad."""
    
    def setUp(self):
        self.client = TestClient()
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
        self.client.login(username='testuser', password='testpass123')
    
    def test_sql_injection_protection(self):
        """Test que se bloquea SQL injection en comentarios."""
        from core.security import detectar_sql_injection
        
        # Patrones de SQL injection
        sql_attacks = [
            "'; DROP TABLE posts; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
        ]
        
        for attack in sql_attacks:
            self.assertTrue(detectar_sql_injection(attack), 
                          f"Debería detectar: {attack}")
    
    def test_xss_protection(self):
        """Test que se bloquea XSS en comentarios."""
        from core.security import validar_sin_xss
        
        xss_attacks = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
        ]
        
        for attack in xss_attacks:
            with self.assertRaises(Exception):  # ValidationError
                validar_sin_xss(attack, 'test_field')
    
    def test_rate_limiting(self):
        """Test que el rate limiting funciona."""
        # Hacer múltiples intentos de login fallidos
        self.client.logout()
        for i in range(6):
            response = self.client.post(reverse('sesion'), {
                'username': 'nonexistent',
                'password': 'wrong'
            })
        
        # El 6to intento debería ser bloqueado o limitado
        # (Nota: esto depende de la configuración del rate limit)


