HAMACA DIGITAL
Laboratorio de Antropologia de la Innovacion
Documento interno · Confidencial · Agosto 2026
Arquitectura AntrolabsHD
AntrolabsHD es la aplicacion Android nativa que fusiona la deteccion y curaduria de prospectos (dominio antes cubierto por RadarHD) con el instrumento de campo para ejecutar el Peritaje de Rigor Cualitativo (dominio de AntroSapiens). AntroSapiens permanece como proyecto independiente, sin modificacion de su base de codigo ni de su proposito actual.
00 · Resumen ejecutivo
Este documento fija la arquitectura de AntrolabsHD tal como se armonizo entre el marco institucional de Hamaca Digital (Cinco Palancas, Axioma Raiz, logica de Expediente) y el estado tecnico real del Motor A (hd_scraper), incluyendo la reparacion en curso de la costura organizacion-candidato-prospecto-expediente-evidencia (BC-I y BC-II).
La decision operativa confirmada define tres ejes: un modelo de estado hibrido que correlaciona la capa tecnica, la capa institucional y la capa de presentacion; una conectividad hibrida donde el Peritaje corre embebido localmente via Chaquopy y la prospeccion consume el backend remoto de RadarHD; y una secuencia de construccion que avanza ambos dominios en paralelo, pantalla por pantalla.
01 · Identidad y alcance
AntrolabsHD no reemplaza a AntroSapiens ni a RadarHD como sistemas independientes; los fusiona en una sola superficie de uso para el fundador, respetando la frontera de Motor A definida en las auditorias tecnicas: el motor estructura evidencia y candidatos, la decision comercial de contactar sigue siendo exclusivamente humana.
Dominio
Origen
Funcion en AntrolabsHD
Prospeccion
RadarHD (Motor A)
Deteccion, triage, curaduria de decisor y expediente comercial
Peritaje
AntroSapiens (Motor B)
Mesa de Evidencias, Mesa de Relaciones, Dictamen del Peritaje contratado
AntroSapiens
Proyecto independiente
No se modifica; existe en paralelo sin integracion

02 · Armonizacion con las Cinco Palancas
Cada componente tecnico de AntrolabsHD se ancla explicitamente a uno de los cinco principios estructurales de HD. Esta tabla es la referencia obligatoria para evaluar si una pantalla, endpoint o flujo nuevo pertenece al sistema.
Palanca HD
Componente tecnico
Correspondencia
Epistemologica
G0 (guardia de admisibilidad de senal)
Extiende la logica de kappa mayor o igual a 0.8 a la etapa de deteccion de prospectos, antes del corpus del Peritaje
Posicional
Radar (deteccion en Capa 0)
Interviene antes del producto, la interfaz o el growth del prospecto
Territorial
Mesa de Relaciones (SubjetLand)
Acervo acumulativo visible solo post-Peritaje; invisible y no referenciable en prospeccion fria
De Escala
Separacion Motor A / decision Mario
El sistema estructura evidencia; la decision de activar un expediente es exclusiva del fundador
Relacional
Certificado de Rigor
Estado de cierre explicito; ningun producto se ofrece automaticamente tras la certificacion

El Axioma Raiz ("si sientes que tienes que convencer, soltaste las palancas") se traduce tecnicamente en una regla dura: ninguna pantalla de AntrolabsHD puede iniciar contacto automatizado con un prospecto. Toda transicion hacia intencion comercial requiere una accion deliberada del fundador.
03 · Arquitectura de tres capas de estado
El modelo de estados confirmado no elige entre el vocabulario del audit tecnico y el vocabulario institucional de HD; los correlaciona en tres capas explicitas, siguiendo el mapeo exigido en la Fase 3 del audit: backend, estado cientifico, estado comercial, estado UI.
Capa
Vocabulario
Gobernada por
Tecnica
Detectado / Observado / Descartado
Motor A, guardia G0
Institucional
Abierto / En Cuarentena / Admisible / Activado / Archivado
Logica de Expediente HD, decision del fundador
Presentacion
Circulo Detectado / Medio circulo Observado / Circulo lleno Fijado / Rombo Incorporado al Sprint
UI, sin logica de negocio propia


Tabla de correlacion
Estado tecnico
Condicion
Estado institucional
Marcador UI
Detectado
Senal capturada por radar, sin validar
Abierto
Circulo Detectado
Observado
Paso G0, ICP incompleto
En Cuarentena
Medio circulo Observado
Observado
ICP completo, cita textual verificable
Admisible
Circulo lleno Fijado
(decision humana)
Fundador activa el expediente
Activado
Rombo Incorporado al Sprint
Descartado
No supera G0 o criterios ICP
Archivado
(sin marcador, fuera de vista activa)

04 · Arquitectura de conectividad hibrida
La conectividad se decide por dominio, no por preferencia tecnica unica. El Peritaje corre embebido localmente porque es trabajo artesanal offline sobre corpus de cliente, protegido por Kill Switch, sin dependencia de senales externas en vivo. La prospeccion consume el backend remoto porque depende de fuentes vivas y de un backend en reparacion activa (costura BC-I y BC-II), cuya copia no debe duplicarse dentro del APK para evitar desincronizacion.
Dominio
Modo
Justificacion
Peritaje
Local, embebido via Chaquopy
Offline, artesanal, protegido por Kill Switch, sin fuentes externas en vivo
Prospeccion
Remoto, contra RadarHD en Vercel y Neon
Depende de fuentes vivas (Google News, GDELT, Hunter.io) y de un backend en reparacion activa

El motor Python embebido via Chaquopy (hd_scraper completo, FastAPI, pydantic 1.10, apscheduler) construido y verificado durante esta sesion queda reasignado exclusivamente al dominio de Peritaje. No se descarta; se acota a la mitad del sistema para la que es la arquitectura correcta.
05 · Secuencia de construccion
Ambos dominios avanzan en paralelo, una pantalla a la vez, siguiendo el orden de dependencia funcional confirmado.
Orden
Pantalla
Dominio
Conectividad
1
Radar
Prospeccion
Remota
2
Candidatos / Triage
Prospeccion
Remota
3
Expediente
Prospeccion
Remota, escritura de transicion institucional
4
Mesa de Evidencias
Peritaje
Local
5
Mesa de Relaciones
Peritaje
Local
6
Dictamen y Certificado
Peritaje
Local

06 · Riesgos y deuda tecnica
Desincronizacion de estado del repositorio: se registraron tres conteos distintos de tests en sesiones separadas (832, 854, 871 pasando) sobre el mismo repositorio, senal de que multiples sesiones avanzan sin sincronizarse entre si. Debe confirmarse el commit de referencia antes de construir sobre Motor A.
La costura BC-I y BC-II (identidad referencial organizacion, candidato, prospecto, expediente, evidencia) esta en reparacion activa segun la auditoria mas reciente. AntrolabsHD no debe construirse contra un estado de esa costura que no este confirmado como estable.
El motor local embebido (Chaquopy) refleja la copia de hd_scraper existente al momento de esta sesion. Si la reparacion de la costura modifica el modelo de datos, la copia local usada para Peritaje debe resincronizarse antes de considerarse vigente.
Ningun endpoint remoto de prospeccion debe exponer una accion de contacto automatico. Cualquier boton o llamada que dispare contacto sin decision explicita del fundador viola el Axioma Raiz y debe rechazarse en revision.
07 · Reglas de gobernanza
Ninguna IA decide a que candidato contactar. La priorizacion es informativa; la decision es exclusivamente del fundador.
AntrolabsHD no se convierte en CRM generico. La navegacion y el lenguaje siguen la logica pericial de HD, no la logica de gestion de relaciones comerciales.
G0 permanece como guardia epistemologica sobre toda senal antes de que un candidato avance de estado.
El Kill Switch del Peritaje (interferencia del cliente, carga del fundador superior a 65 horas en dos semanas) se conserva sin cambios en el dominio local.
Ningun estado institucional (Admisible, Activado) se alcanza sin cita textual verificable y sin los tres criterios ICP simultaneos: interlocutor con poder de decision, ronda reciente de 6 a 12 meses, sintoma declarado por el propio operador.
08 · Proximos pasos
Confirmar el commit de referencia de hd_scraper y resolver la desincronizacion de conteo de tests entre sesiones.
Verificar el estado actual de la reparacion BC-I y BC-II antes de conectar la pantalla de Radar a los endpoints remotos.
Disenar el contrato de API remota (rutas, payloads, autenticacion) entre AntrolabsHD y RadarHD para las pantallas de Radar, Candidatos y Expediente.
Construir la pantalla de Radar como primera unidad funcional, siguiendo el orden de la seccion 05.

Hamaca Digital · Laboratorio de Antropologia de la Innovacion · Documento interno · Agosto 2026
