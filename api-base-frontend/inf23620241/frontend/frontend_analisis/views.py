from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
import requests
import json
from django.utils.dateparse import parse_datetime
from django.utils import formats
from datetime import datetime

# Vista para la página principal
def index(req):
    return render(req, 'index.html')

# Vista para la página del mecánico
def mecanico(req, rut):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    incidencia_url = f"http://backend:8000/incidencia/"
    mecanicos_asignados_url = f"http://backend:8000/MecanicosAsignados/"

    incidencia_respuesta = requests.get(incidencia_url)
    mecanico_respuesta = requests.get(mecanico_url)
    mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url)

    incidencia_data = incidencia_respuesta.json()
    mecanico_data = mecanico_respuesta.json()
    mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

    # Filtrar incidencias asignadas al mecánico actual y convertir las fechas
    incidencias_asignadas = []
    for incidencia in incidencia_data:
        if any(asignacion['mecanico'] == rut and asignacion['incidencia'] == incidencia['id'] for asignacion in mecanicos_asignados_data):
            if not incidencia['estado']:  # Verifica si el estado es False
                incidencia['fecha_inicio'] = parse_datetime(incidencia['fecha_inicio'])
                incidencia['fecha_termino'] = parse_datetime(incidencia['fecha_termino'])
                incidencias_asignadas.append(incidencia)


    # Agregar contexto messages
    return render(req, 'mecanico.html', {"incidencias": incidencias_asignadas, "mecanico": mecanico_data, "messages": messages.get_messages(req)})

def incidencia(req, rut, id):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    incidencia_url = f"http://backend:8000/incidencia/{id}/"
    progreso_url = f"http://backend:8000/progreso/"
    mecanicos_url = f"http://backend:8000/mecanico/"
    mecanicos_asignados_url = f"http://backend:8000/MecanicosAsignados/"

    if req.method == 'POST':
        print("POST data received:", req.POST)  

        data = {
            "fecha_progreso": timezone.now().isoformat(),
            "descripcion": req.POST['descripcion'],
            "mecanico": req.POST['mecanico'],
            "incidencia": req.POST['incidencia']
        }

        estado_str = req.POST['estado'].strip().lower()
        estado_bool = estado_str == 'true'

        incidencia_respuesta = requests.get(incidencia_url)
        incidencia_data = incidencia_respuesta.json()
        data2 = {
            "fecha_inicio": incidencia_data['fecha_inicio'],
            "fecha_termino": incidencia_data['fecha_termino'],
            "descripcion": incidencia_data['descripcion'],
            "estado": estado_bool,
            "motor": incidencia_data['motor'],
            "tipo_incidencia": incidencia_data['tipo_incidencia']
        }

        #print("Data for PUT request:", data2)  

        headers = {'Content-Type': 'application/json'}

        try:
            respuesta = requests.post(progreso_url, json=data, headers=headers)
            print("Progreso POST response status code:", respuesta.status_code)
            print("Progreso POST response content:", respuesta.content)
            
            respuesta_put = requests.put(incidencia_url, json=data2, headers=headers)
            print("Incidencia PUT response status code:", respuesta_put.status_code)
            print("Incidencia PUT response content:", respuesta_put.content)

            if respuesta.status_code == 201 and respuesta_put.status_code in [200, 204]:
               
                if estado_bool:
                    return redirect('mecanico', rut=rut)
                else:
                    return redirect('incidencia', rut=rut, id=id)
            else:
                messages.error(req, f'Error al guardar el progreso o actualizar el estado: {respuesta.status_code}, {respuesta_put.status_code}')
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    try:
        mecanico_respuesta = requests.get(mecanico_url)
        mecanicos_respuesta = requests.get(mecanicos_url)
        incidencia_respuesta = requests.get(incidencia_url)
        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url)
        progreso_respuesta = requests.get(progreso_url, params={'incidencia_id': id})

        if (incidencia_respuesta.status_code == 200 and 
            progreso_respuesta.status_code == 200):

            incidencia_data = incidencia_respuesta.json()
            progreso_data = progreso_respuesta.json()
            mecanico_data = mecanico_respuesta.json()
            mecanicos_data = mecanicos_respuesta.json()
            mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

            motor_url = f"http://backend:8000/motor/{incidencia_data['motor']}/"

            motor_respuesta = requests.get(motor_url)
            motor_data = motor_respuesta.json()

            for progreso in progreso_data:
                progreso['fecha_progreso'] = parse_datetime(progreso['fecha_progreso'])

            incidencia_data['fecha_inicio'] = parse_datetime(incidencia_data['fecha_inicio'])
            incidencia_data['fecha_termino'] = parse_datetime(incidencia_data['fecha_termino'])

            mecanicos_asignados_a_incidencia = [
                asignacion['mecanico'] for asignacion in mecanicos_asignados_data
                if asignacion['incidencia'] == id
            ]

            mecanicos_asignados = [
                mecanico for mecanico in mecanicos_data
                if mecanico['rut'] in mecanicos_asignados_a_incidencia
            ]

            return render(req, 'incidencia.html', {
                "incidencia": incidencia_data,
                "progresos": progreso_data,
                "mecanico": mecanico_data,
                "mecanicos": mecanicos_data,
                "mecanicos_asignados": mecanicos_asignados,
                "motor": motor_data
            })

    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'incidencia.html', {"error": "Error al obtener los datos de la incidencia o progreso"})

# Vista para crear una nueva incidencia
@csrf_exempt
def crear_incidencia(req, rut):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    motores_url = f"http://backend:8000/motor/"

    motores_respuesta = requests.get(motores_url)
    mecanico_respuesta = requests.get(mecanico_url)

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

        print("Datos enviados en la solicitud POST:", data)  # Depuración: Imprimir datos enviados

        try:
            response = requests.post(URL, json=data, headers=headers)
            response.raise_for_status()

            if response.status_code == 201:
                return redirect(reverse('mecanico', kwargs={'rut': rut}))
            else:
                messages.error(req, 'Error al crear la incidencia.')
                print("Error al crear la incidencia:", response.json())  # Depuración: Imprimir contenido de la respuesta

        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                # Capturar respuesta de error 400 y mostrar mensaje específico sobre la fecha
                if e.response.status_code == 400:
                    messages.error(req, 'Error al crear la incidencia: La fecha de término debe ser superior a la fecha actual.')

                    print("Respuesta de error 400 del servidor:", e.response.content)  # Depuración: Imprimir contenido de la respuesta de error
                else:
                    messages.error(req, f'Error en la solicitud: {str(e)}')
                    print("Excepción al crear la incidencia:", str(e))  # Depuración: Imprimir excepción

        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')
            print("Excepción al crear la incidencia:", str(e))  # Depuración: Imprimir excepción

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
        
        # Realizar la petición a la URL externa con el rut
        URL = "http://backend:8000/mecanico/"
        response = requests.get(URL, params={'rut': rut})

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Buscar el mecánico en la lista
                mecanico = next((item for item in data if item.get('rut') == rut), None)
                if mecanico:
                    # Verificar si la contraseña es correcta
                    if mecanico.get('contraseña') == password:
                        # Redirigir a la vista 'mecanico' con el rut
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

# Vista para la página del jefe de motores
def ingresar_cuenta_JM(req):
    if req.method == 'POST':
        rut = req.POST.get('rut')
        password = req.POST.get('contraseña')
        
        # Realizar la petición a la URL externa con el rut
        URL = "http://backend:8000/JefeMotores/"
        response = requests.get(URL, params={'rut': rut})

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Buscar el mecánico en la lista
                jefe_motores = next((item for item in data if item.get('rut') == rut), None)
                if jefe_motores:
                    # Verificar si la contraseña es correcta
                    if jefe_motores.get('contraseña') == password:
                        return redirect('incidencias_sin_asignar')  # Redirigir a la vista 'mecanico' si las credenciales son correctas
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
    
    if req.method == 'POST':
        data = {
            'mecanico': req.POST.get('mecanico'),
            'incidencia': id,
            'fecha_asignacion':timezone.now().isoformat()
        }
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(mecanicos_asignados_url, json=data, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 201:
                return redirect(reverse('incidencias_sin_asignar'))
            else:
                messages.error(req, 'Error al asignar el mecánico.')
        
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    mecanicos_respuesta = requests.get(mecanicos_url)
    if mecanicos_respuesta.status_code != 200:
        print(f"Error obteniendo mecanicos: {mecanicos_respuesta.status_code}")
    else:
        print(f"Datos de mecanicos: {mecanicos_respuesta.json()}")

    mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url)
    if mecanicos_asignados_respuesta.status_code != 200:
        print(f"Error obteniendo mecanicos asignados: {mecanicos_asignados_respuesta.status_code}")
    else:
        print(f"Datos de mecanicos asignados: {mecanicos_asignados_respuesta.json()}")

    incidencia_respuesta = requests.get(incidencia_url)
    if incidencia_respuesta.status_code != 200:
        print(f"Error obteniendo incidencia: {incidencia_respuesta.status_code}")
    else:
        print(f"Datos de incidencia: {incidencia_respuesta.json()}")

    incidencia_data = incidencia_respuesta.json()
    mecanicos_asignados_data = mecanicos_asignados_respuesta.json()
    mecanicos_data = mecanicos_respuesta.json()

    incidencia_data['fecha_inicio'] = parse_datetime(incidencia_data['fecha_inicio'])
    incidencia_data['fecha_termino'] = parse_datetime(incidencia_data['fecha_termino'])

    # Filtrar mecánicos no asignados
    mecanicos_asignados_ids = [asignacion['mecanico'] for asignacion in mecanicos_asignados_data if asignacion['incidencia'] == id]
    mecanicos_no_asignados = [mecanico for mecanico in mecanicos_data if mecanico['rut'] not in mecanicos_asignados_ids and mecanico['disponibilidad'] == True]

    return render(req, 'asignar_mecanico.html', {
        "incidencia": incidencia_data, 
        "mecanicos": mecanicos_data, 
        "mecanicos_no_asignados": mecanicos_no_asignados,
        "mecanicos_asignados": [mecanico for mecanico in mecanicos_data if mecanico['rut'] in mecanicos_asignados_ids]
    })

# Vista para crear una nueva incidencia
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
        response = requests.post(URL, json=data, headers=headers)

        if response.status_code == 201:
            return redirect(reverse('ingresar_cuenta'))
        else:
            # Manejar el caso donde la API devuelve un error
            print("Error:", response.status_code)
            print(response.json())
            return render(req, 'crear_cuenta_mecanico.html', {'error': response.json()})

    return render(req, 'crear_cuenta_mecanico.html')

def incidencias_sin_asignar_view(req):
    incidencia_url = "http://backend:8000/incidencia/"
    mecanicos_asignados_url = "http://backend:8000/MecanicosAsignados/"
    motores_url = f"http://backend:8000/motor/"
    
    motores_respuesta = requests.get(motores_url)
    motores_respuesta.raise_for_status()
    motores_data = motores_respuesta.json()

    mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url)
    incidencia_respuesta = requests.get(incidencia_url)

    incidencia_data = incidencia_respuesta.json()
    mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

    for incidencia in incidencia_data:
        incidencia['fecha_inicio'] = parse_datetime(incidencia['fecha_inicio'])
        incidencia['fecha_termino'] = parse_datetime(incidencia['fecha_termino'])
        asignaciones = [asignacion for asignacion in mecanicos_asignados_data if asignacion['incidencia'] == incidencia['id']]
        if asignaciones:
            incidencia['mecanicos_asignados'] = len(asignaciones)
        else:
            incidencia['mecanicos_asignados'] = 'sin asignar'

    filtro = req.GET.get('filtro', 'todas')

    if filtro == 'sin_asignar':
        incidencias_filtradas = [incidencia for incidencia in incidencia_data if incidencia['mecanicos_asignados'] == 'sin asignar']
    elif filtro == 'asignadas':
        incidencias_filtradas = [incidencia for incidencia in incidencia_data if incidencia['mecanicos_asignados'] != 'sin asignar']
    else:
        incidencias_filtradas = incidencia_data

    incidencias_en_progreso = [incidencia for incidencia in incidencias_filtradas if not incidencia['estado']]

    return render(req, 'incidencias_sin_asignar.html', {"incidencias": incidencias_en_progreso, 
                                                        "filtro": filtro,
                                                        "motores":motores_data})

def motores_view(req):
    motores_url = f"http://backend:8000/motor/"
    estado = req.GET.get('estado', '')  # Obtén el parámetro de filtro 'estado' de la URL
    
    try:
        motores_respuesta = requests.get(motores_url)
        motores_respuesta.raise_for_status()
        motores_data = motores_respuesta.json()
        
        if estado and estado != 'Todos':
            motores_data = [motor for motor in motores_data if motor['estado'].lower() == estado.lower()]
        
    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener los datos de los motores: {str(e)}')
        motores_data = []

    return render(req, 'motores.html', {'motores': motores_data, 'estado': estado})

@csrf_exempt
def crear_motor(req):
    motor_url = f"http://backend:8000/motor/"
    if req.method == 'POST':
        try:
            data = {
                "n_serie": req.POST['n_serie'],
                "marca": req.POST['marca'],
                "estado": req.POST['estado']
            }
        except KeyError as e:
            messages.error(req, f'Falta el campo {e}')
            return render(req, 'crear_motor.html')
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(motor_url, json=data, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 201:
                return redirect(reverse('motores_view'))
            else:
                messages.error(req, 'Error al crear el motor.')
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')
    
    return render(req, 'crear_motor.html')

def editar_motores(req, id):
    motor_url = f"http://backend:8000/motor/{id}/"
    historial_asignacion_motor_url = f"http://backend:8000/HistorialMotorCamion/"
    try:
        historial_asignacion_motor_respuesta = requests.get(historial_asignacion_motor_url)
        historial_asignacion_motor_respuesta.raise_for_status()
        historial_asignacion_motor_data = historial_asignacion_motor_respuesta.json()
    
        motor_respuesta = requests.get(motor_url)
        motor_respuesta.raise_for_status()
        motor_data = motor_respuesta.json()

    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener los datos del motor: {str(e)}')
        motor_data = {}
        
    if req.method == 'POST' and req.POST.get('_method') == 'DELETE':
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.delete(motor_url, headers=headers)
            if response.status_code == 204:
                # Incidencia eliminada exitosamente
                return redirect('motores_view')  
            else:
                messages.error(req, 'Error al eliminar la incidencia.')
        except requests.exceptions.RequestException as e:
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
                    respuesta_delete = requests.delete(url, headers=headers)
                    respuesta_delete.raise_for_status()
        try:
            respuesta_put = requests.put(motor_url, json=data, headers=headers)
            respuesta_put.raise_for_status()
            if respuesta_put.status_code in [200, 204]:
                #messages.success(req, 'Estado y camión del motor actualizados exitosamente.')
                return redirect('motores_view')
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'editar_motor.html', {'motor': motor_data})

def historial_incidencias(req):
    incidencia_url = "http://backend:8000/incidencia/"
    motores_url = "http://backend:8000/motor/"

    incidencia_respuesta = requests.get(incidencia_url)
    motores_respuesta = requests.get(motores_url)

    incidencia_data = incidencia_respuesta.json()
    motores_data = motores_respuesta.json()

    numero_motor = req.GET.get('numero_motor')
    estado = req.GET.get('estado')

    if numero_motor and numero_motor != "":
        incidencia_data = [incidencia for incidencia in incidencia_data if str(incidencia['motor']) == numero_motor]

    if estado and estado != "":
        estado_bool = estado.lower() == 'true'
        incidencia_data = [incidencia for incidencia in incidencia_data if incidencia['estado'] == estado_bool]
    
    incidencias_en_progreso = 0
    incidencias_finalizadas = 0
    incidencias_fallas = 0
    incidencias_programadas = 0
    for incidencia in incidencia_data:
        if incidencia['tipo_incidencia'] == 'Por Falla':
            incidencias_fallas += 1
        if incidencia['tipo_incidencia'] == 'Programada':
            incidencias_programadas += 1
        if not incidencia['estado']:
            incidencias_en_progreso += 1
        if incidencia['estado']:
            incidencias_finalizadas += 1

    return render(req, 'historial_incidencias.html', {"incidencias": incidencia_data,
                                                       "motores": motores_data,
                                                       "incidencias_en_progreso": incidencias_en_progreso,
                                                       "incidencias_finalizadas": incidencias_finalizadas,
                                                       "incidencias_programadas":incidencias_programadas,
                                                       "incidencias_fallas": incidencias_fallas
                                                       })
# Vista para crear una nueva incidencia

def incidencia_JM(req, id):
    incidencia_url = f"http://backend:8000/incidencia/{id}/"
    progreso_url = f"http://backend:8000/progreso/"
    mecanicos_url = f"http://backend:8000/mecanico/"
    mecanicos_asignados_url = f"http://backend:8000/MecanicosAsignados/"

    if req.method == 'POST' and req.POST.get('_method') == 'DELETE':
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.delete(incidencia_url, headers=headers)
            if response.status_code == 204:
                # Incidencia eliminada exitosamente
                return redirect('historial_incidencias')  
            else:
                messages.error(req, 'Error al eliminar la incidencia.')
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')
        return render(req, 'incidencia_JM.html', {"error": "Error al eliminar la incidencia"})
    
    try:
        incidencia_respuesta = requests.get(incidencia_url)
        progreso_respuesta = requests.get(progreso_url, params={'incidencia_id': id})
        mecanicos_respuesta = requests.get(mecanicos_url)
        mecanicos_asignados_respuesta = requests.get(mecanicos_asignados_url)

        if (incidencia_respuesta.status_code == 200 and 
            progreso_respuesta.status_code == 200):

            incidencia_data = incidencia_respuesta.json()
            progreso_data = progreso_respuesta.json()
            mecanicos_data = mecanicos_respuesta.json()
            mecanicos_asignados_data = mecanicos_asignados_respuesta.json()

            motor_url = f"http://backend:8000/motor/{incidencia_data['motor']}/"
            motor_respuesta = requests.get(motor_url)
            motor_data = motor_respuesta.json()

            for progreso in progreso_data:
                progreso['fecha_progreso'] = parse_datetime(progreso['fecha_progreso'])

            incidencia_data['fecha_inicio'] = parse_datetime(incidencia_data['fecha_inicio'])
            incidencia_data['fecha_termino'] = parse_datetime(incidencia_data['fecha_termino'])

            mecanicos_asignados_a_incidencia = [
                asignacion['mecanico'] for asignacion in mecanicos_asignados_data
                if asignacion['incidencia'] == id
            ]

            mecanicos_asignados = [
                mecanico for mecanico in mecanicos_data
                if mecanico['rut'] in mecanicos_asignados_a_incidencia
            ]
            
            progresos_por_mecanico ={}
            for progreso in progreso_data:
                if not progreso['mecanico'] in progresos_por_mecanico:
                    progresos_por_mecanico[progreso['mecanico']] = 0
                if progreso['incidencia'] == id:
                    progresos_por_mecanico[progreso['mecanico']] += 1

            progresos_lista = [(rut, cantidad) for rut, cantidad in progresos_por_mecanico.items()]
            return render(req, 'incidencia_JM.html', {
                "incidencia": incidencia_data,
                "progresos": progreso_data,
                "mecanicos": mecanicos_data,
                "mecanicos_asignados": mecanicos_asignados,
                "motor": motor_data,
                "progresos_por_mecanico": progresos_lista
            })

    except requests.exceptions.RequestException as e:
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
        response = requests.post(URL, json=data, headers=headers)

        if response.status_code == 201:
            return redirect(reverse('ingresar_cuenta_JM'))
        else:
            # Manejar el caso donde la API devuelve un error
            print("Error:", response.status_code)
            print(response.json())
            return render(req, 'crear_cuenta_JM.html', {'error': response.json()})

    return render(req, 'crear_cuenta_JM.html')

def perfil_mecanico(req, rut):
    mecanico_url = f"http://backend:8000/mecanico/{rut}/"
    try:
        mecanico_respuesta = requests.get(mecanico_url)
        mecanico_respuesta.raise_for_status()
        mecanico_data = mecanico_respuesta.json()
    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener los datos del motor: {str(e)}')
        mecanico_data = {}

    if req.method == 'POST':
        if req.POST['disponibilidad'] == "Si":
            disponibilidad = True
        else:
             disponibilidad = False
        data = {
            "nombre": mecanico_data['nombre'],
            "rut": mecanico_data['rut'],
            "contraseña": mecanico_data['contraseña'],
            "disponibilidad": disponibilidad 
        }
        headers = {'Content-Type': 'application/json'}
        try:
            respuesta_put = requests.put(mecanico_url, json=data, headers=headers)
            respuesta_put.raise_for_status()
            if respuesta_put.status_code in [200, 204]:
                #messages.success(req, 'Estado y camión del motor actualizados exitosamente.')
                return redirect(reverse('mecanico', kwargs={'rut': rut}))
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'perfil_mecanico.html', {'mecanico': mecanico_data})


def camiones(req):
    camiones_url = f"http://backend:8000/camion/"
    asignaciones_motores_url = f"http://backend:8000/HistorialMotorCamion/"
    
    estado = req.GET.get('estado', '')

    try:
        camiones_respuesta = requests.get(camiones_url)
        camiones_respuesta.raise_for_status()
        camiones_data = camiones_respuesta.json()

        asignaciones_motores_respuesta = requests.get(asignaciones_motores_url)
        asignaciones_motores_respuesta.raise_for_status()
        asignaciones_motores_data = asignaciones_motores_respuesta.json()
        
    except requests.exceptions.RequestException as e:
        messages.error(req, f'Error al obtener los datos de los camiones: {str(e)}')
        camiones_data = []
        asignaciones_motores_data = []

    camiones_asignados = [histcamion['camion'] for histcamion in asignaciones_motores_data]

    # Filtrar camiones según el estado seleccionado
    if estado == 'Sin asignar':
        camiones_data = [camion for camion in camiones_data if camion['patente'] not in camiones_asignados]
    elif estado == 'Asignado':
        camiones_data = [camion for camion in camiones_data if camion['patente'] in camiones_asignados]

    return render(req, 'camiones.html', {"camiones": camiones_data,
                                         "asignaciones_motores": asignaciones_motores_data,
                                         "camiones_asignados": camiones_asignados,
                                         "estado": estado
                                         })

def crear_camion(req):
    camiones_url = f"http://backend:8000/camion/"
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
            response = requests.post(camiones_url, json=data, headers=headers)
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
    asignaciones_motores_url = f"http://backend:8000/HistorialMotorCamion/"
    motores_url = f"http://backend:8000/motor/"

    asignaciones_motores_respuesta = requests.get(asignaciones_motores_url)
    asignaciones_motores_respuesta.raise_for_status()
    asignaciones_motores_data = asignaciones_motores_respuesta.json()

    motores_respuesta = requests.get(motores_url)
    motores_respuesta.raise_for_status()
    motores_data = motores_respuesta.json()

    camion_respuesta = requests.get(camion_url)
    camion_respuesta.raise_for_status()
    camion_data = camion_respuesta.json()

    
    motores_asignados = [historialMotor['motor'] for historialMotor in asignaciones_motores_data ] 
    motores_operativos_sin_asignar = [motor['id'] for motor in motores_data if motor['estado'] == 'Operativo' and not motor['id'] in motores_asignados]
    
    print(motores_operativos_sin_asignar)
    
    if req.method == 'POST' and motores_operativos_sin_asignar:

        data = {
            'fecha_retiro': req.POST.get('fecha_retiro'),
            'fecha_asignacion': timezone.now().isoformat(),
            'motor': req.POST.get('motor'),
            'camion': id
        }
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(asignaciones_motores_url, json=data, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 201:
                return redirect(reverse('camiones'))
            else:
                messages.error(req, 'Error al asignar el motor.')
        
        except requests.exceptions.RequestException as e:
            messages.error(req, f'Error en la solicitud: {str(e)}')

    return render(req, 'asignacion_motor.html', {
        "motores_operativos": motores_operativos_sin_asignar,
        "camion": camion_data,
        "motores": motores_data
    })

def ver_asignacion_camion(req, id):
    camion_url = f"http://backend:8000/camion/{id}/"
    asignaciones_url = f"http://backend:8000/HistorialMotorCamion/"
    motores_url = f"http://backend:8000/motor/"
    
    motores_respuesta = requests.get(motores_url)
    motores_respuesta.raise_for_status()
    motores_data = motores_respuesta.json()

    asignaciones_respuesta = requests.get(asignaciones_url)
    asignaciones_respuesta.raise_for_status()
    asignaciones_data = asignaciones_respuesta.json()

    camion_respuesta = requests.get(camion_url)
    camion_respuesta.raise_for_status()
    camion_data = camion_respuesta.json()

    asignacion = []
    for asign in asignaciones_data:
        if id == asign['camion']:
            asignacion = asign
    motor_asignado = []
    for motor in motores_data:
        if motor['id'] == asignacion ['motor']:
            motor_asignado = motor


    return render(req, "ver_asignacion_camion.html",{"camion": camion_data,
                                                     "asignacion": asignacion,
                                                     "motor": motor_asignado
                                                     })
    
def ingreso_antecedente(req):
    camiones_url = f"http://backend:8000/camion/"

    camiones_respuesta = requests.get(camiones_url)
    
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
            response = requests.post(URL, json=data, headers=headers)
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

    # Obtener todos los motores para el menú desplegable
    motores_respuesta = requests.get(motores_url)
    camiones_respuesta = requests.get(camiones_url)

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
    motorcamion_respuesta = requests.get(motorcamion_url)
    motorcamion_data = motorcamion_respuesta.json()

    # Filtrar el último registro de asignación del motor seleccionado
    asignacion_actual = None
    for asignacion in reversed(motorcamion_data):
        if str(asignacion['motor']) == motor_id:
            asignacion_actual = asignacion
            break

    antecedentes_data = []
    if asignacion_actual:
        # Obtener los antecedentes del camión actual
        antecedentes_respuesta = requests.get(antecedentes_url, params={'camion': asignacion_actual['camion']})
        antecedentes_data = antecedentes_respuesta.json()

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