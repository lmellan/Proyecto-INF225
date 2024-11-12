from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
import requests
from django.utils.dateparse import parse_datetime
from django.utils import formats
from datetime import datetime


TIMEOUT_DURATION = 10  # Timeout de 10 segundos


# Vista para la página principal
def index(req):
    return render(req, 'index.html')

# Vista para la página del mecánico
def mecanico(req, rut):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    incidencia_url = f"http://backend:8000/incidencia/"
    mecanicos_asignados_url = f"http://backend:8000/MecanicosAsignados/"
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        incidencia_respuesta = requests.get(incidencia_url, timeout=timeout_duration)
        mecanico_respuesta = requests.get(mecanico_url, timeout=timeout_duration)
        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url, timeout=timeout_duration)

        if incidencia_respuesta.status_code == 200:
            incidencia_data = incidencia_respuesta.json()
        else:
            incidencia_data = []
        
        if mecanico_respuesta.status_code == 200:
            mecanico_data = mecanico_respuesta.json()
        else:
            mecanico_data = {}

        if mecanicos_asignados_respuesta.status_code == 200:
            mecanicos_asignados_data = mecanicos_asignados_respuesta.json()
        else:
            mecanicos_asignados_data = []

    except requests.RequestException as e:
        messages.error(req, f"Error de conexión con el backend: {e}")
        return render(req, 'mecanico.html', {"incidencias": [], "mecanico": {}, "messages": messages.get_messages(req)})

    incidencias_asignadas = []
    for incidencia in incidencia_data:
        if any(asignacion['mecanico'] == rut and asignacion['incidencia'] == incidencia['id'] for asignacion in mecanicos_asignados_data):
            if not incidencia['estado']:
                incidencia['fecha_inicio'] = parse_datetime(incidencia['fecha_inicio'])
                incidencia['fecha_termino'] = parse_datetime(incidencia['fecha_termino'])
                incidencias_asignadas.append(incidencia)

    return render(req, 'mecanico.html', {"incidencias": incidencias_asignadas, "mecanico": mecanico_data, "messages": messages.get_messages(req)})


def incidencia(req, rut, id):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    incidencia_url = f"http://backend:8000/incidencia/{id}/"
    progreso_url = "http://backend:8000/progreso/"
    mecanicos_url = "http://backend:8000/mecanico/"
    mecanicos_asignados_url = "http://backend:8000/MecanicosAsignados/"
    timeout_duration = 10  # Timeout de 10 segundos

    if req.method == 'POST':
        data = {
            "fecha_progreso": timezone.now().isoformat(),
            "descripcion": req.POST['descripcion'],
            "mecanico": req.POST['mecanico'],
            "incidencia": req.POST['incidencia']
        }
        estado_bool = req.POST['estado'].strip().lower() == 'true'

        try:
            incidencia_respuesta = requests.get(incidencia_url, timeout=timeout_duration)
            incidencia_data = incidencia_respuesta.json()
            data2 = {
                "fecha_inicio": incidencia_data['fecha_inicio'],
                "fecha_termino": incidencia_data['fecha_termino'],
                "descripcion": incidencia_data['descripcion'],
                "estado": estado_bool,
                "motor": incidencia_data['motor'],
                "tipo_incidencia": incidencia_data['tipo_incidencia']
            }
            headers = {'Content-Type': 'application/json'}

            respuesta = requests.post(progreso_url, json=data, headers=headers, timeout=timeout_duration)
            respuesta_put = requests.put(incidencia_url, json=data2, headers=headers, timeout=timeout_duration)

            if respuesta.status_code == 201 and respuesta_put.status_code in [200, 204]:
                if estado_bool:
                    return redirect('mecanico', rut=rut)
                else:
                    return redirect('incidencia', rut=rut, id=id)
            else:
                messages.error(req, 'Error al guardar el progreso o actualizar el estado.')
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    try:
        mecanico_respuesta = requests.get(mecanico_url, timeout=timeout_duration)
        mecanicos_respuesta = requests.get(mecanicos_url, timeout=timeout_duration)
        incidencia_respuesta = requests.get(incidencia_url, timeout=timeout_duration)
        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url, timeout=timeout_duration)
        progreso_respuesta = requests.get(progreso_url, params={'incidencia_id': id}, timeout=timeout_duration)

        if incidencia_respuesta.status_code == 200 and progreso_respuesta.status_code == 200:
            incidencia_data = incidencia_respuesta.json()
            progreso_data = progreso_respuesta.json()
            mecanico_data = mecanico_respuesta.json()
            mecanicos_data = mecanicos_respuesta.json()
            mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

            motor_url = f"http://backend:8000/motor/{incidencia_data['motor']}/"
            motor_respuesta = requests.get(motor_url, timeout=timeout_duration)
            motor_data = motor_respuesta.json()

            for progreso in progreso_data:
                progreso['fecha_progreso'] = parse_datetime(progreso['fecha_progreso'])

            incidencia_data['fecha_inicio'] = parse_datetime(incidencia_data['fecha_inicio'])
            incidencia_data['fecha_termino'] = parse_datetime(incidencia_data['fecha_termino'])

            mecanicos_asignados_a_incidencia = [
                asignacion['mecanico'] for asignacion in mecanicos_asignados_data if asignacion['incidencia'] == id
            ]

            mecanicos_asignados = [
                mecanico for mecanico in mecanicos_data if mecanico['rut'] in mecanicos_asignados_a_incidencia
            ]

            return render(req, 'incidencia.html', {
                "incidencia": incidencia_data,
                "progresos": progreso_data,
                "mecanico": mecanico_data,
                "mecanicos": mecanicos_data,
                "mecanicos_asignados": mecanicos_asignados,
                "motor": motor_data
            })

    except requests.RequestException as e:
        messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'incidencia.html', {"error": "Error al obtener los datos de la incidencia o progreso"})


@csrf_exempt
def crear_incidencia(req, rut):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    motores_url = "http://backend:8000/motor/"
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        motores_respuesta = requests.get(motores_url, timeout=timeout_duration)
        mecanico_respuesta = requests.get(mecanico_url, timeout=timeout_duration)
    except requests.RequestException as e:
        messages.error(req, f'Error en la solicitud: {str(e)}')
        return render(req, 'crear_incidencia.html', {'rut': rut, 'error': 'Error al obtener datos del servidor'})

    if req.method == 'POST':
        data = {
            'fecha_termino': req.POST.get('fecha_termino'),
            'descripcion': req.POST.get('descripcion'),
            'motor': req.POST.get('motor'),
            'fecha_inicio': timezone.now().isoformat(),
            'estado': False,
            'tipo_incidencia': req.POST.get('tipo_incidencia'),
        }
        URL = "http://backend:8000/incidencia/"
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(URL, json=data, headers=headers, timeout=timeout_duration)
            response.raise_for_status()

            if response.status_code == 201:
                return redirect(reverse('mecanico', kwargs={'rut': rut}))
            else:
                messages.error(req, 'Error al crear la incidencia.')

        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    if mecanico_respuesta.status_code == 200:
        mecanico_data = mecanico_respuesta.json()
        motores_data = motores_respuesta.json()
        return render(req, 'crear_incidencia.html', {'rut': rut, 'mecanico': mecanico_data, 'motores': motores_data})
    else:
        return render(req, 'crear_incidencia.html', {'rut': rut, 'error': 'Error al obtener datos del mecánico'})


def ingresar_cuenta_mecanico(req):
    if req.method == 'POST':
        rut = req.POST.get('rut')
        password = req.POST.get('contraseña')
        
        URL = "http://backend:8000/mecanico/"
        response = requests.get(URL, params={'rut': rut}, timeout=10)  # Timeout de 10 segundos

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                mecanico = next((item for item in data if item.get('rut') == rut), None)
                if mecanico:
                    if mecanico.get('contraseña') == password:
                        return redirect('mecanico', rut=mecanico['rut'])
                    else:
                        messages.error(req, f'Contraseña incorrecta.')
                else:
                    messages.error(req, 'Rut no encontrado.')
            else:
                messages.error(req, 'Formato de respuesta inesperado.')
        else:
            messages.error(req, 'Error al conectar con el servidor.')

    return render(req, 'ingresar_cuenta.html')


def ingresar_cuenta_JM(req):
    if req.method == 'POST':
        rut = req.POST.get('rut')
        password = req.POST.get('contraseña')
        
        URL = "http://backend:8000/JefeMotores/"
        response = requests.get(URL, params={'rut': rut}, timeout=10)  # Timeout de 10 segundos

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                jefe_motores = next((item for item in data if item.get('rut') == rut), None)
                if jefe_motores:
                    if jefe_motores.get('contraseña') == password:
                        return redirect('incidencias_sin_asignar')
                    else:
                        messages.error(req, f'Contraseña incorrecta.')
                else:
                    messages.error(req, 'Rut no encontrado.')
            else:
                messages.error(req, 'Formato de respuesta inesperado.')
        else:
            messages.error(req, 'Error al conectar con el servidor.')

    return render(req, 'ingresar_cuenta_JM.html')


def asignar_mecanico(req, id):
    incidencia_url = f"http://backend:8000/incidencia/{id}/"
    mecanicos_asignados_url = "http://backend:8000/MecanicosAsignados/"
    mecanicos_url = "http://backend:8000/mecanico/"
    timeout_duration = 10

    if req.method == 'POST':
        data = {
            'mecanico': req.POST.get('mecanico'),
            'incidencia': id,
            'fecha_asignacion': timezone.now().isoformat()
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(mecanicos_asignados_url, json=data, headers=headers, timeout=timeout_duration)
            response.raise_for_status()

            if response.status_code == 201:
                return redirect(reverse('incidencias_sin_asignar'))
            else:
                messages.error(req, 'Error al asignar el mecánico.')
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    try:
        mecanicos_respuesta = requests.get(mecanicos_url, timeout=timeout_duration)
        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url, timeout=timeout_duration)
        incidencia_respuesta = requests.get(incidencia_url, timeout=timeout_duration)

        incidencia_data = incidencia_respuesta.json()
        mecanicos_asignados_data = mecanicos_asignados_respuesta.json()
        mecanicos_data = mecanicos_respuesta.json()

        incidencia_data['fecha_inicio'] = parse_datetime(incidencia_data['fecha_inicio'])
        incidencia_data['fecha_termino'] = parse_datetime(incidencia_data['fecha_termino'])

        mecanicos_asignados_ids = [asignacion['mecanico'] for asignacion in mecanicos_asignados_data if asignacion['incidencia'] == id]
        mecanicos_no_asignados = [mecanico for mecanico in mecanicos_data if mecanico['rut'] not in mecanicos_asignados_ids and mecanico['disponibilidad']]

        return render(req, 'asignar_mecanico.html', {
            "incidencia": incidencia_data,
            "mecanicos": mecanicos_data,
            "mecanicos_no_asignados": mecanicos_no_asignados,
            "mecanicos_asignados": [mecanico for mecanico in mecanicos_data if mecanico['rut'] in mecanicos_asignados_ids]
        })

    except requests.RequestException as e:
        messages.error(req, f'Error en la solicitud: {str(e)}')
        return render(req, 'asignar_mecanico.html', {"error": "Error al obtener datos de la incidencia o mecánicos."})


@csrf_exempt

def crear_cuenta_mecanico(req):
    if req.method == 'POST':
        data = {
            'rut': req.POST['rut'],
            'nombre': req.POST['nombre'],
            'contraseña': req.POST['contraseña'],
            "disponibilidad": True,
        }
        URL = "http://backend:8000/mecanico/"
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(URL, json=data, headers=headers, timeout=TIMEOUT_DURATION)
            if response.status_code == 201:
                return redirect(reverse('ingresar_cuenta'))
            else:
                print("Error:", response.status_code)
                print(response.json())
                return render(req, 'crear_cuenta_mecanico.html', {'error': response.json()})
                
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')


    return render(req, 'crear_cuenta_mecanico.html')


def incidencias_sin_asignar_view(req):
    incidencia_url = "http://backend:8000/incidencia/"
    mecanicos_asignados_url = "http://backend:8000/MecanicosAsignados/"
    motores_url = "http://backend:8000/motor/"
    timeout_duration = 10

    try:
        motores_respuesta = requests.get(motores_url, timeout=timeout_duration)
        motores_respuesta.raise_for_status()
        motores_data = motores_respuesta.json()

        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url, timeout=timeout_duration)
        incidencia_respuesta = requests.get(incidencia_url, timeout=timeout_duration)

        incidencia_data = incidencia_respuesta.json()
        mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

        for incidencia in incidencia_data:
            incidencia['fecha_inicio'] = parse_datetime(incidencia['fecha_inicio'])
            incidencia['fecha_termino'] = parse_datetime(incidencia['fecha_termino'])
            asignaciones = [asignacion for asignacion in mecanicos_asignados_data if asignacion['incidencia'] == incidencia['id']]
            incidencia['mecanicos_asignados'] = len(asignaciones) if asignaciones else 'sin asignar'

    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos de las incidencias: {str(e)}')
        motores_data = []
        incidencia_data = []

    filtro = req.GET.get('filtro', 'todas')
    incidencias_filtradas = [incidencia for incidencia in incidencia_data if incidencia['mecanicos_asignados'] == 'sin asignar'] if filtro == 'sin_asignar' else incidencia_data
    incidencias_en_progreso = [incidencia for incidencia in incidencias_filtradas if not incidencia['estado']]

    return render(req, 'incidencias_sin_asignar.html', {"incidencias": incidencias_en_progreso, "filtro": filtro, "motores": motores_data})


def motores_view(req):
    motores_url = "http://backend:8000/motor/"
    estado = req.GET.get('estado', '')
    timeout_duration = 10

    try:
        motores_respuesta = requests.get(motores_url, timeout=timeout_duration)
        motores_respuesta.raise_for_status()
        motores_data = motores_respuesta.json()

        if estado and estado != 'Todos':
            motores_data = [motor for motor in motores_data if motor['estado'].lower() == estado.lower()]

    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos de los motores: {str(e)}')
        motores_data = []

    return render(req, 'motores.html', {'motores': motores_data, 'estado': estado})


@csrf_exempt
def crear_motor(req):
    motor_url = "http://backend:8000/motor/"
    if req.method == 'POST':
        data = {
            "n_serie": req.POST['n_serie'],
            "marca": req.POST['marca'],
            "estado": req.POST['estado']
        }
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(motor_url, json=data, headers=headers, timeout=10)
            response.raise_for_status()

            if response.status_code == 201:
                return redirect(reverse('motores_view'))
            else:
                messages.error(req, 'Error al crear el motor.')
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'crear_motor.html')


def editar_motores(req, id):
    motor_url = f"http://backend:8000/motor/{id}/"
    historial_asignacion_motor_url = "http://backend:8000/HistorialMotorCamion/"
    timeout_duration = 10

    try:
        historial_asignacion_motor_respuesta = requests.get(historial_asignacion_motor_url, timeout=timeout_duration)
        historial_asignacion_motor_respuesta.raise_for_status()
        historial_asignacion_motor_data = historial_asignacion_motor_respuesta.json()

        motor_respuesta = requests.get(motor_url, timeout=timeout_duration)
        motor_respuesta.raise_for_status()
        motor_data = motor_respuesta.json()

    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos del motor: {str(e)}')
        motor_data = {}

    if req.method == 'POST' and req.POST.get('_method') == 'DELETE':
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.delete(motor_url, headers=headers, timeout=timeout_duration)
            response.raise_for_status()

            if response.status_code == 204:
                return redirect('motores_view')
            else:
                messages.error(req, 'Error al eliminar el motor.')
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')
        return render(req, 'motores.html', {"error": "Error al eliminar el motor"})

    if req.method == 'POST':
        data = {
            "n_serie": motor_data['n_serie'],
            "marca": motor_data['marca'],
            "estado": req.POST['estado']
        }
        headers = {'Content-Type': 'application/json'}

        if req.POST['estado'] == "Averiado":
            for ham in historial_asignacion_motor_data:
                if ham['motor'] == id:
                    url = f"http://backend:8000/HistorialMotorCamion/{ham['id']}"
                    requests.delete(url, headers=headers, timeout=timeout_duration).raise_for_status()
        try:
            requests.put(motor_url, json=data, headers=headers, timeout=timeout_duration).raise_for_status()
            return redirect('motores_view')
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'editar_motor.html', {'motor': motor_data})


def historial_incidencias(req):
    incidencia_url = "http://backend:8000/incidencia/"
    motores_url = "http://backend:8000/motor/"

    try:
        incidencia_respuesta = requests.get(incidencia_url, timeout=TIMEOUT_DURATION)
        motores_respuesta = requests.get(motores_url, timeout=TIMEOUT_DURATION)

        incidencia_data = incidencia_respuesta.json()
        motores_data = motores_respuesta.json()

    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos de incidencias o motores: {str(e)}')
        incidencia_data = []
        motores_data = []

    numero_motor = req.GET.get('numero_motor')
    estado = req.GET.get('estado')

    if numero_motor:
        incidencia_data = [incidencia for incidencia in incidencia_data if str(incidencia['motor']) == numero_motor]

    if estado:
        estado_bool = estado.lower() == 'true'
        incidencia_data = [incidencia for incidencia in incidencia_data if incidencia['estado'] == estado_bool]

    incidencias_en_progreso = sum(1 for i in incidencia_data if not i['estado'])
    incidencias_finalizadas = sum(1 for i in incidencia_data if i['estado'])
    incidencias_fallas = sum(1 for i in incidencia_data if i['tipo_incidencia'] == 'Por Falla')
    incidencias_programadas = sum(1 for i in incidencia_data if i['tipo_incidencia'] == 'Programada')

    return render(req, 'historial_incidencias.html', {
        "incidencias": incidencia_data,
        "motores": motores_data,
        "incidencias_en_progreso": incidencias_en_progreso,
        "incidencias_finalizadas": incidencias_finalizadas,
        "incidencias_programadas": incidencias_programadas,
        "incidencias_fallas": incidencias_fallas
    })


def incidencia_JM(req, id):
    incidencia_url = f"http://backend:8000/incidencia/{id}/"
    progreso_url = "http://backend:8000/progreso/"
    mecanicos_url = "http://backend:8000/mecanico/"
    mecanicos_asignados_url = "http://backend:8000/MecanicosAsignados/"

    if req.method == 'POST' and req.POST.get('_method') == 'DELETE':
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.delete(incidencia_url, headers=headers, timeout=TIMEOUT_DURATION)
            if response.status_code == 204:
                return redirect('historial_incidencias')
            else:
                messages.error(req, 'Error al eliminar la incidencia.')
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')
        return render(req, 'incidencia_JM.html', {"error": "Error al eliminar la incidencia"})

    try:
        incidencia_respuesta = requests.get(incidencia_url, timeout=TIMEOUT_DURATION)
        progreso_respuesta = requests.get(progreso_url, params={'incidencia_id': id}, timeout=TIMEOUT_DURATION)
        mecanicos_respuesta = requests.get(mecanicos_url, timeout=TIMEOUT_DURATION)
        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url, timeout=TIMEOUT_DURATION)

        if incidencia_respuesta.status_code == 200 and progreso_respuesta.status_code == 200:
            incidencia_data = incidencia_respuesta.json()
            progreso_data = progreso_respuesta.json()
            mecanicos_data = mecanicos_respuesta.json()
            mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

            motor_url = f"http://backend:8000/motor/{incidencia_data['motor']}/"
            motor_respuesta = requests.get(motor_url, timeout=TIMEOUT_DURATION)
            motor_data = motor_respuesta.json()

            for progreso in progreso_data:
                progreso['fecha_progreso'] = parse_datetime(progreso['fecha_progreso'])

            incidencia_data['fecha_inicio'] = parse_datetime(incidencia_data['fecha_inicio'])
            incidencia_data['fecha_termino'] = parse_datetime(incidencia_data['fecha_termino'])

            mecanicos_asignados = [mecanico for mecanico in mecanicos_data if mecanico['rut'] in {asignacion['mecanico'] for asignacion in mecanicos_asignados_data if asignacion['incidencia'] == id}]

            progresos_por_mecanico = {progreso['mecanico']: 0 for progreso in progreso_data}
            for progreso in progreso_data:
                if progreso['incidencia'] == id:
                    progresos_por_mecanico[progreso['mecanico']] += 1

            return render(req, 'incidencia_JM.html', {
                "incidencia": incidencia_data,
                "progresos": progreso_data,
                "mecanicos": mecanicos_data,
                "mecanicos_asignados": mecanicos_asignados,
                "motor": motor_data,
                "progresos_por_mecanico": list(progresos_por_mecanico.items())
            })

    except requests.RequestException as e:
        messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'incidencia_JM.html', {"error": "Error al obtener los datos de la incidencia o progreso"})


@csrf_exempt
def crear_cuenta_JM(req):
    if req.method == 'POST':
        data = {
            'rut': req.POST['rut'],
            'nombre': req.POST['nombre'],
            'contraseña': req.POST['contraseña'],
        }
        URL = "http://backend:8000/JefeMotores/"
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(URL, json=data, headers=headers, timeout=TIMEOUT_DURATION)
            if response.status_code == 201:
                return redirect(reverse('ingresar_cuenta_JM'))
            else:
                print("Error:", response.status_code)
                print(response.json())
                return render(req, 'crear_cuenta_JM.html', {'error': response.json()})
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'crear_cuenta_JM.html')


def perfil_mecanico(req, rut):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"

    try:
        mecanico_respuesta = requests.get(mecanico_url, timeout=TIMEOUT_DURATION)
        mecanico_respuesta.raise_for_status()
        mecanico_data = mecanico_respuesta.json()
    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos del mecánico: {str(e)}')
        mecanico_data = {}

    if req.method == 'POST':
        disponibilidad = req.POST['disponibilidad'] == "Si"
        data = {
            "nombre": mecanico_data['nombre'],
            "rut": mecanico_data['rut'],
            "contraseña": mecanico_data['contraseña'],
            "disponibilidad": disponibilidad
        }
        headers = {'Content-Type': 'application/json'}
        try:
            respuesta_put = requests.put(mecanico_url, json=data, headers=headers, timeout=TIMEOUT_DURATION)
            respuesta_put.raise_for_status()
            if respuesta_put.status_code in [200, 204]:
                return redirect(reverse('mecanico', kwargs={'rut': rut}))
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'perfil_mecanico.html', {'mecanico': mecanico_data})



def camiones(req):
    camiones_url = "http://backend:8000/camion/"
    asignaciones_motores_url = "http://backend:8000/HistorialMotorCamion/"
    estado = req.GET.get('estado', '')
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        camiones_respuesta = requests.get(camiones_url, timeout=timeout_duration)
        camiones_respuesta.raise_for_status()
        camiones_data = camiones_respuesta.json()

        asignaciones_motores_respuesta = requests.get(asignaciones_motores_url, timeout=timeout_duration)
        asignaciones_motores_respuesta.raise_for_status()
        asignaciones_motores_data = asignaciones_motores_respuesta.json()

    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos de los camiones: {str(e)}')
        camiones_data = []
        asignaciones_motores_data = []

    camiones_asignados = {histcamion['camion'] for histcamion in asignaciones_motores_data}
    if estado == 'Sin asignar':
        camiones_data = [camion for camion in camiones_data if camion['patente'] not in camiones_asignados]
    elif estado == 'Asignado':
        camiones_data = [camion for camion in camiones_data if camion['patente'] in camiones_asignados]

    return render(req, 'camiones.html', {
        "camiones": camiones_data,
        "asignaciones_motores": asignaciones_motores_data,
        "camiones_asignados": camiones_asignados,
        "estado": estado
    })

def crear_camion(req):
    camiones_url = f"http://backend:8000/camion/"
    timeout_duration = 10  # Timeout de 10 segundos

    if req.method == 'POST':
        try:
            data = {
                "patente": req.POST['patente'],
                "marca": req.POST['marca'],
                "modelo": req.POST['modelo']
            }
        except KeyError as e:
            messages.error(req, f'Falta el campo {e}')
            return render(req, 'camiones.html')
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(camiones_url, json=data, headers=headers, timeout=timeout_duration)
            response.raise_for_status()
            
            if response.status_code == 201:
                return redirect(reverse('camiones'))
            else:
                messages.error(req, 'Error al registrar camión.')
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')
    
    return render(req, 'crear_camion.html')

def asignacion_motor(req, id):
    camion_url = f"http://backend:8000/camion/{id}/"
    asignaciones_motores_url = "http://backend:8000/HistorialMotorCamion/"
    motores_url = "http://backend:8000/motor/"
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        asignaciones_motores_respuesta = requests.get(asignaciones_motores_url, timeout=timeout_duration)
        motores_respuesta = requests.get(motores_url, timeout=timeout_duration)
        camion_respuesta = requests.get(camion_url, timeout=timeout_duration)

        asignaciones_motores_data = asignaciones_motores_respuesta.json()
        motores_data = motores_respuesta.json()
        camion_data = camion_respuesta.json()

    except requests.RequestException as e:
        messages.error(req, f'Error en la solicitud: {str(e)}')
        return render(req, 'asignacion_motor.html', {"error": "Error al obtener datos del camión o motor."})

    motores_asignados = {historialMotor['motor'] for historialMotor in asignaciones_motores_data}
    motores_operativos_sin_asignar = [motor['id'] for motor in motores_data if motor['estado'] == 'Operativo' and motor['id'] not in motores_asignados]

    if req.method == 'POST' and motores_operativos_sin_asignar:
        data = {
            'fecha_retiro': req.POST.get('fecha_retiro'),
            'fecha_asignacion': timezone.now().isoformat(),
            'motor': req.POST.get('motor'),
            'camion': id
        }
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(asignaciones_motores_url, json=data, headers=headers, timeout=timeout_duration)
            response.raise_for_status()
            if response.status_code == 201:
                return redirect(reverse('camiones'))
            else:
                messages.error(req, 'Error al asignar el motor.')
        
        except requests.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'asignacion_motor.html', {
        "motores_operativos": motores_operativos_sin_asignar,
        "camion": camion_data,
        "motores": motores_data
    })

def ver_asignacion_camion(req, id):
    camion_url = f"http://backend:8000/camion/{id}/"
    asignaciones_url = "http://backend:8000/HistorialMotorCamion/"
    motores_url = "http://backend:8000/motor/"
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        motores_respuesta = requests.get(motores_url, timeout=timeout_duration)
        asignaciones_respuesta = requests.get(asignaciones_url, timeout=timeout_duration)
        camion_respuesta = requests.get(camion_url, timeout=timeout_duration)

        motores_data = motores_respuesta.json()
        asignaciones_data = asignaciones_respuesta.json()
        camion_data = camion_respuesta.json()

    except requests.RequestException as e:
        messages.error(req, f'Error al obtener los datos de los camiones o motores: {str(e)}')
        return render(req, "ver_asignacion_camion.html", {"error": "Error al obtener los datos del camión o motor."})

    asignacion = next((asign for asign in asignaciones_data if asign['camion'] == id), None)
    motor_asignado = next((motor for motor in motores_data if motor['id'] == asignacion['motor']), None) if asignacion else None

    return render(req, "ver_asignacion_camion.html", {
        "camion": camion_data,
        "asignacion": asignacion,
        "motor": motor_asignado
    })

def ingreso_antecedente(req):
    camiones_url = f"http://backend:8000/camion/"
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        camiones_respuesta = requests.get(camiones_url, timeout=timeout_duration)
    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener los camiones: {str(e)}')
        return render(req, "ingreso_antecedente.html", {"error": "Error al obtener los camiones."})

    context = {}

    if req.method == 'POST':
        data = {
            'fecha_registro': timezone.now().isoformat(),
            'descripcion': req.POST.get('descripcion'),
            'camion': req.POST.get('camion'),
            'nombre': req.POST.get('nombre'),
        }
        URL = "http://backend:8000/HistorialAntecedentes/"
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(URL, json=data, headers=headers, timeout=timeout_duration)
            response.raise_for_status()

            if response.status_code == 201:
                context['success'] = True  # Indica que el registro fue exitoso
            else:
                context['error'] = 'Error al registrar el antecedente.'
        
        except requests.exceptions.RequestException as e:
            context['error'] = f'Error en la solicitud: {str(e)}'
        
    if camiones_respuesta.status_code == 200:
        camiones_data = camiones_respuesta.json()
        context['camiones'] = camiones_data
    
    return render(req, 'ingreso_antecedente.html', context)


def antecedentes(req, rut):
    antecedentes_url = "http://backend:8000/HistorialAntecedentes/"
    motorcamion_url = "http://backend:8000/HistorialMotorCamion/"
    motores_url = "http://backend:8000/motor/"
    camiones_url = "http://backend:8000/camion/"
    timeout_duration = 10  # Timeout de 10 segundos

    try:
        motores_respuesta = requests.get(motores_url, timeout=timeout_duration)
        camiones_respuesta = requests.get(camiones_url, timeout=timeout_duration)
    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener los datos: {str(e)}')
        return render(req, "antecedentes.html", {"error": "Error al obtener los motores o camiones."})

    motores_data = motores_respuesta.json()
    camiones_data = camiones_respuesta.json()

    # Verificar si se seleccionó un motor
    motor_id = req.GET.get('motor_id')
    if not motor_id and motores_data:
        # Si no se seleccionó ningún motor, usar el primero en la lista
        motor_id = str(motores_data[0]['id'])
    else:
        motor_id = str(motor_id)  # Asegurar que motor_id sea cadena

    # Obtener el motor seleccionado
    motor_data = next((motor for motor in motores_data if str(motor['id']) == motor_id), None)
    
    # Obtener historial de asignaciones de motores a camiones
    try:
        motorcamion_respuesta = requests.get(motorcamion_url, timeout=timeout_duration)
        motorcamion_data = motorcamion_respuesta.json()
    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener el historial de asignaciones: {str(e)}')
        return render(req, "antecedentes.html", {"error": "Error al obtener las asignaciones de motor a camión."})

    # Filtrar el último registro de asignación del motor seleccionado
    asignacion_actual = None
    for asignacion in reversed(motorcamion_data):
        if str(asignacion['motor']) == motor_id:
            asignacion_actual = asignacion
            break

    antecedentes_data = []
    if asignacion_actual:
        # Obtener los antecedentes del camión actual
        try:
            antecedentes_respuesta = requests.get(antecedentes_url, params={'camion': asignacion_actual['camion']}, timeout=timeout_duration)
            antecedentes_data = antecedentes_respuesta.json()
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error al obtener los antecedentes: {str(e)}')
            return render(req, "antecedentes.html", {"error": "Error al obtener los antecedentes."})

        # Filtrar solo los antecedentes para el camión específico
        antecedentes_data = [antecedente for antecedente in antecedentes_data if str(antecedente['camion']) == str(asignacion_actual['camion'])]

    # Obtener el camión actual para el título y la información
    camion_actual = next((camion for camion in camiones_data if str(camion['patente']) == str(asignacion_actual['camion'])), None) if asignacion_actual else None

    # Pasar los datos al contexto
    return render(req, 'antecedentes.html', {
        "motores": motores_data,
        "motor": motor_data,
        "antecedentes": antecedentes_data,
        "rut": rut,
        "camion": camion_actual
    })
