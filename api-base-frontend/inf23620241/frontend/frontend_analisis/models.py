from django.db import models

class Motor(models.Model):
    n_serie = models.CharField(max_length=256)
    marca = models.CharField(max_length=256)
    estado = models.CharField(max_length=256)

class Mecanico(models.Model):
    rut = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=256)
    contraseña = models.CharField(max_length=20, default='default_password')
    disponibilidad = models.BooleanField()

class Incidencia(models.Model):
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_termino = models.DateTimeField()
    descripcion = models.TextField()
    estado = models.BooleanField()
    tipo_incidencia = models.CharField(max_length=256)

class Progreso(models.Model):
    mecanico = models.ForeignKey(Mecanico, on_delete=models.CASCADE)
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE)
    fecha_progreso = models.DateTimeField(null=True, blank=True)  # Hacer opcional
    descripcion = models.TextField(null=True, blank=True)  # Hacer opcional

class JefeMotores(models.Model):
    rut = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=256)
    contraseña = models.CharField(max_length=20, default='default_password')

class MecanicosAsignados(models.Model):
    mecanico = models.ForeignKey(Mecanico, on_delete=models.CASCADE)
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE)


class Camion(models.Model):
    patente = models.CharField(max_length=256, primary_key=True)
    marca = models.CharField(max_length=256)
    modelo = models.CharField(max_length=256)

class HistorialMotorCamion(models.Model):
    fecha_retiro = models.DateTimeField()
    fecha_asignacion = models.DateTimeField()
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE)
    camion = models.ForeignKey(Camion, on_delete=models.CASCADE)

class HistorialAntecedentes(models.Model):
    fecha_registro = models.DateTimeField()
    nombre = models.CharField(max_length=256)
    descripcion = models.TextField()
    camion = models.ForeignKey(Camion, on_delete=models.CASCADE)
    