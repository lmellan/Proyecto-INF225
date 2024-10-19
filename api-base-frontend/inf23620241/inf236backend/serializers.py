from rest_framework import serializers
from .models import Motor, Mecanico, Incidencia, Progreso, JefeMotores, MecanicosAsignados, Camion, HistorialMotorCamion, HistorialAntecedentes

class MotorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motor
        fields = '__all__'

class MecanicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mecanico
        fields = '__all__'

class IncidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidencia
        fields = '__all__'

    def validate(self, data):

        fecha_inicio = data.get('fecha_inicio')
        fecha_termino = data.get('fecha_termino')

        if fecha_termino and fecha_inicio and fecha_termino < fecha_inicio:
            raise serializers.ValidationError("La fecha de término no puede ser menor que la fecha de inicio.")

        return data

class ProgresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progreso
        fields = '__all__'

class JefeMotoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = JefeMotores
        fields = '__all__'

class MecanicosAsignadosSerializer(serializers.ModelSerializer):
    class Meta:
        model = MecanicosAsignados
        fields = '__all__'

class CamionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camion
        fields = '__all__'

class HistorialMotorCamionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialMotorCamion
        fields = '__all__'

class HistorialAntecedentesSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialAntecedentes
        fields = '__all__'
