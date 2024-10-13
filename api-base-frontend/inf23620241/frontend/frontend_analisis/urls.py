from django.urls import path 
from . import views 

urlpatterns = [
    path('', views.index, name="index"),
    path('mecanico/<str:rut>/', views.mecanico, name='mecanico'),
    path('mecanico/<str:rut>/incidencia/<int:id>/', views.incidencia, name="incidencia"),
    path('mecanico/<str:rut>/crear_incidencia/', views.crear_incidencia, name='crear_incidencia'),
    path('crear_cuenta_mecanico/', views.crear_cuenta_mecanico, name='crear_cuenta_mecanico'),
    path('ingresar_cuenta/', views.ingresar_cuenta_mecanico, name='ingresar_cuenta'),
    path('crear_cuenta_JM/', views.crear_cuenta_JM, name='crear_cuenta_JM'),
    path('ingresar_cuenta_JM/', views.ingresar_cuenta_JM, name='ingresar_cuenta_JM'),
    path('incidencias_sin_asignar/', views.incidencias_sin_asignar_view, name='incidencias_sin_asignar'),
    path('asignar_mecanico/incidencia/<int:id>/', views.asignar_mecanico, name='asignar_mecanico'),
    path('motores/', views.motores_view, name='motores_view'),
    path('crear_motor/', views.crear_motor, name='crear_motor'),
    path('motores<int:id>/', views.editar_motores, name='editar_motores'),
    path('historial_incidencias/', views.historial_incidencias, name='historial_incidencias'), 
    path('incidencia_JM/<int:id>/', views.incidencia_JM, name='incidencia_JM'),
    path('perfil_mecanico/<str:rut>/', views.perfil_mecanico, name='perfil_mecanico'),
    path('camiones/', views.camiones, name='camiones'),
    path('crear_camion/', views.crear_camion, name='crear_camion'),
    path('asignacion_motor/<str:id>/', views.asignacion_motor, name='asignacion_motor'),
    path('ver_asignacion_camion/<str:id>/', views.ver_asignacion_camion, name='ver_asignacion_camion'),
    path('ingreso_antecedente/', views.ingreso_antecedente, name='ingreso_antecedente'),
    path('mecanico/<str:rut>/antecedentes/', views.antecedentes, name='antecedentes'),

]  