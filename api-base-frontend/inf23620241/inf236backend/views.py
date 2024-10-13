from rest_framework import viewsets, filters
from rest_framework.response import Response
from .models import Motor, Mecanico, Incidencia, Progreso, JefeMotores, MecanicosAsignados, Camion, HistorialMotorCamion, HistorialAntecedentes
from .serializers import MotorSerializer, MecanicoSerializer, IncidenciaSerializer, ProgresoSerializer, JefeMotoresSerializer, MecanicosAsignadosSerializer, CamionSerializer, HistorialMotorCamionSerializer, HistorialAntecedentesSerializer
 
# ViewSet para el modelo Motor
class MotorViewSet(viewsets.ModelViewSet):
    queryset = Motor.objects.all()
    serializer_class = MotorSerializer

# ViewSet para el modelo Mecanico
class MecanicoViewSet(viewsets.ModelViewSet):
    queryset = Mecanico.objects.all() 
    serializer_class = MecanicoSerializer

# ViewSet para el modelo Incidencia
class IncidenciaViewSet(viewsets.ModelViewSet):
    queryset = Incidencia.objects.all()
    serializer_class = IncidenciaSerializer

# ViewSet para el modelo Progreso
class ProgresoViewSet(viewsets.ModelViewSet):
    queryset = Progreso.objects.all()
    serializer_class = ProgresoSerializer

# ViewSet para el modelo JefeMotores
class JefeMotoresViewSet(viewsets.ModelViewSet):
    queryset = JefeMotores.objects.all()
    serializer_class = JefeMotoresSerializer

class MecanicosAsignadosViewSet(viewsets.ModelViewSet):
    queryset = MecanicosAsignados.objects.all()
    serializer_class = MecanicosAsignadosSerializer

class CamionViewSet(viewsets.ModelViewSet):
    queryset = Camion.objects.all()
    serializer_class = CamionSerializer

# ViewSet para el modelo HistorialMotorCamion
class HistorialMotorCamionViewSet(viewsets.ModelViewSet):
    queryset = HistorialMotorCamion.objects.all()
    serializer_class = HistorialMotorCamionSerializer

class HistorialAntecedentesViewSet(viewsets.ModelViewSet):
    queryset = HistorialAntecedentes.objects.all()
    serializer_class = HistorialAntecedentesSerializer
 