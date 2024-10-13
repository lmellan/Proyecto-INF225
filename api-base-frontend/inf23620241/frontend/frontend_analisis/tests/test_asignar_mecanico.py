from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from ..models import Mecanico, Incidencia, Motor
from django.utils import timezone

class AsignarMecanicoTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
        # Configuración de la URL para la vista `asignar_mecanico` con un id de incidencia específico
        cls.asignar_mecanico_url = reverse('asignar_mecanico', args=[1])

    @patch('frontend_analisis.models.Mecanico.objects.create')
    @patch('frontend_analisis.models.Motor.objects.create')
    @patch('frontend_analisis.models.Incidencia.objects.create')
    @patch('requests.post')
    @patch('requests.get')
    def test_asignacion_exitosa(self, mock_get, mock_post, mock_incidencia_create, mock_motor_create, mock_mecanico_create):
        """
        Prueba la asignación exitosa de un mecánico disponible a una incidencia.
        """
        # Crear objetos simulados de Mecanico, Motor e Incidencia
        mock_mecanico = Mecanico(rut='12345678-9', nombre='Jorge Perez', contraseña='password123', disponibilidad=True)
        mock_motor = Motor(n_serie='1234', marca='Yamaha', estado='Operativo')
        mock_incidencia = Incidencia(
            id=1,
            motor=mock_motor,
            fecha_inicio=timezone.now(),
            fecha_termino=timezone.now() + timezone.timedelta(days=3),
            descripcion='Motor sobrecalentado',
            estado=False,
            tipo_incidencia='Por falla'
        )
        
        # Configurar los mocks para devolver las instancias simuladas al llamarse
        mock_mecanico_create.return_value = mock_mecanico
        mock_motor_create.return_value = mock_motor
        mock_incidencia_create.return_value = mock_incidencia
        
        # Simular las respuestas GET para obtener datos del mecánico, mecánicos asignados e incidencia
        mock_get.side_effect = [
            type('Response', (object,), {
                'status_code': 200, 
                'json': lambda: [{'rut': '12345678-9', 'nombre': 'Jorge Perez', 'disponibilidad': True}]
            })(), # Respuesta simulada para mecánicos disponibles
            type('Response', (object,), {
                'status_code': 200, 
                'json': lambda: [{'mecanico': '12345678-9', 'incidencia': 1}]
            })(), # Respuesta simulada para mecánicos asignados
            type('Response', (object,), {
                'status_code': 200, 
                'json': lambda: {
                    'id': 1,
                    'motor': {'n_serie': '1234'},
                    'fecha_inicio': timezone.now().isoformat(),
                    'fecha_termino': (timezone.now() + timezone.timedelta(days=3)).isoformat(),
                    'descripcion': 'Motor sobrecalentado',
                    'estado': False,
                    'tipo_incidencia': 'Por falla'
                }
            })() # Respuesta simulada para la incidencia
        ]
        
        # Simular una respuesta exitosa de asignación de mecánico (código 201)
        mock_post.return_value.status_code = 201

        # Datos simulados para la asignación de un mecánico
        data = {
            'mecanico': mock_mecanico.rut # Rut del mecánico a asignar
        }

        # Realizar la solicitud POST a la vista `asignar_mecanico`
        response = self.client.post(self.asignar_mecanico_url, data)
        
        # Verificar que el resultado de la solicitud es una redirección (código 302)
        # Esto indica que la asignación del mecánico fue exitosa
        self.assertEqual(response.status_code, 302)

    @patch('frontend_analisis.models.Mecanico.objects.create')
    @patch('frontend_analisis.models.Motor.objects.create')
    @patch('frontend_analisis.models.Incidencia.objects.create')
    @patch('requests.get')
    def test_todos_mecanicos_no_disponibles(self, mock_get, mock_incidencia_create, mock_motor_create, mock_mecanico_create):
        """
        Prueba que la vista `asignar_mecanico` maneja adecuadamente el caso
        en que todos los mecánicos están marcados como no disponibles.
        """
        # Crear objetos simulados de Mecanico, Motor e Incidencia, todos no disponibles
        mock_mecanico_1 = Mecanico(rut='11111111-1', nombre='No Disponible 1', contraseña='password1', disponibilidad=False)
        mock_mecanico_2 = Mecanico(rut='22222222-2', nombre='No Disponible 2', contraseña='password2', disponibilidad=False)
        mock_motor = Motor(n_serie='1234', marca='Yamaha', estado='Operativo')
        mock_incidencia = Incidencia(
            id=1,
            motor=mock_motor,
            fecha_inicio=timezone.now(),
            fecha_termino=timezone.now() + timezone.timedelta(days=3),
            descripcion='Motor sobrecalentado',
            estado=False,
            tipo_incidencia='Por falla'
        )
        
        # Configurar los mocks para devolver las instancias simuladas al llamarse
        mock_mecanico_create.return_value = mock_mecanico_1
        mock_motor_create.return_value = mock_motor
        mock_incidencia_create.return_value = mock_incidencia

        # Simular las respuestas GET donde todos los mecánicos están no disponibles
        mock_get.side_effect = [
            type('Response', (object,), {
                'status_code': 200, 
                'json': lambda _: [
                    {'rut': '11111111-1', 'nombre': 'No Disponible 1', 'disponibilidad': False},
                    {'rut': '22222222-2', 'nombre': 'No Disponible 2', 'disponibilidad': False}
                ]
            })(), # Respuesta simulada para lista de mecánicos
            type('Response', (object,), {
                'status_code': 200, 
                'json': lambda _: []
            })(), # Respuesta simulada para mecánicos asignados
            type('Response', (object,), {
                'status_code': 200, 
                'json': lambda _: {
                    'id': 1,
                    'motor': {'n_serie': '1234'},
                    'fecha_inicio': timezone.now().isoformat(),
                    'fecha_termino': (timezone.now() + timezone.timedelta(days=3)).isoformat(),
                    'descripcion': 'Motor sobrecalentado',
                    'estado': False,
                    'tipo_incidencia': 'Por falla'
                }
            })() # Respuesta simulada para la incidencia
        ]

        # Realizar la solicitud GET para obtener la lista de mecánicos
        response = self.client.get(self.asignar_mecanico_url)
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)

        # Extraer la lista de mecánicos no asignados y disponibles desde el contexto
        mecanicos_no_asignados = response.context['mecanicos_no_asignados']
        
        # Verificar que no hay mecánicos disponibles para asignar
        self.assertEqual(len(mecanicos_no_asignados), 0)

        # Verificar que el mensaje adecuado se muestra en el contenido de la respuesta HTML
        self.assertContains(response, 'No hay mecánicos disponibles para asignar')