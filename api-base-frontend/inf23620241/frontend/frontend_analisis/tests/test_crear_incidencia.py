from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from ..models import Mecanico, Motor
from django.utils import timezone

# Clase de prueba para la vista de creación de incidencias
class CrearIncidenciaTests(TestCase):

    @classmethod
    def setUpClass(cls):
        # Configuración inicial que se ejecuta antes de todas las pruebas en esta clase
        super().setUpClass()
        cls.client = Client()
        # Se genera la URL para la vista de creación de incidencia con un rut dado
        cls.crear_incidencia_url = reverse('crear_incidencia', args=['12345678-9'])

    # Prueba unitaria para la creación exitosa de una incidencia
    @patch('frontend_analisis.models.Mecanico.objects.create')
    @patch('frontend_analisis.models.Motor.objects.create')
    @patch('requests.post')
    @patch('requests.get')
    def test_creacion_exitosa(self, mock_get, mock_post, mock_motor_create, mock_mecanico_create):
        # Simular la creación de objetos Mecanico y Motor
        # Estos mocks reemplazan la creación real en la base de datos para esta prueba
        mock_mecanico = Mecanico(rut='12345678-9', nombre='Jorge Perez', contraseña='password123', disponibilidad=True)
        mock_motor = Motor(n_serie='1234', marca='Yamaha', estado='Operativo')
        
        # Configurar los mocks para devolver las instancias simuladas al llamarse
        mock_mecanico_create.return_value = mock_mecanico
        mock_motor_create.return_value = mock_motor
        
        # Simular la respuesta GET exitosa para obtener datos del mecánico y los motores
        # Esto corresponde a las llamadas que hace la vista `crear_incidencia` al backend
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [
            {'rut': '12345678-9', 'nombre': 'Jorge Perez'}, # Respuesta simulada para el mecánico
            [{'id': 1, 'n_serie': '1234', 'marca': 'Yamaha', 'estado': 'Operativo'}] # Respuesta simulada para el motor
        ]
        
        # Simular una respuesta POST exitosa (código 201 indica creación exitosa)
        # Esto corresponde a la llamada POST que hace la vista al backend para crear la incidencia
        mock_post.return_value.status_code = 201
        
        # Datos simulados del formulario que el cliente enviaría a la vista `crear_incidencia`
        data = {
            'fecha_termino': (timezone.now() - timezone.timedelta(days=3)), # Fecha de terminación de la incidencia
            'descripcion': 'Sobrecalentamiento del motor', # Descripción de la incidencia
            'motor': 1, # ID del motor asociado a la incidencia
            'tipo_incidencia': 'Por falla' # Tipo de incidencia reportada
        }
        
        # Hacer una solicitud POST a la vista usando los datos simulados
        response = self.client.post(self.crear_incidencia_url, data)
        
        # Verificar que el resultado de la solicitud es una redirección (código 302)
        # Esto significa que la incidencia fue creada exitosamente, según la lógica de la vista
        self.assertEqual(response.status_code, 302)

    # Prueba unitaria para el caso donde no existe un motor
    @patch('frontend_analisis.models.Mecanico.objects.create')
    @patch('frontend_analisis.models.Motor.objects.create')
    @patch('requests.post')
    @patch('requests.get')
    def test_motor_no_existe(self, mock_get, mock_post, mock_motor_create, mock_mecanico_create):
        # Simular la creación del objeto Mecanico
        mock_mecanico = Mecanico(rut='12345678-9', nombre='Jorge Perez', contraseña='password123', disponibilidad=True)
        
        # Configurar el mock de creación del mecánico
        mock_mecanico_create.return_value = mock_mecanico
        
        # Simular la respuesta GET exitosa para el mecánico
        mock_get.side_effect = [
            type('Response', (object,), {'status_code': 200, 'json': lambda: {'rut': '12345678-9', 'nombre': 'Jorge Perez'}})(),
            type('Response', (object,), {'status_code': 404})  # Respuesta de error para el motor no encontrado
        ]
        
        # Datos del formulario de creación de incidencia
        data = {
            'fecha_termino': '2024-10-11', # Fecha de terminación de la incidencia
            'descripcion': 'Sobrecalentamiento del motor', # Descripción de la incidencia
            'motor': 999, # ID de un motor no existente
            'tipo_incidencia': 'Por falla' # Tipo de incidencia
        }
        
        # Realizar la solicitud POST a la vista
        response = self.client.post(self.crear_incidencia_url, data)
        
        # Verificar que el resultado es un código 404 debido a que no se encontró el motor
        self.assertEqual(response.status_code, 404)