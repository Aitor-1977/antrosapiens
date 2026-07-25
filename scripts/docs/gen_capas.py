#!/usr/bin/env python3
"""Generador de docs/CAPAS/CAPA_00..18.md — Arquitectura por capas de Motor A.

Los datos están VERIFICADOS contra el código (módulos, endpoints, tablas, tests
reales del repo). Este script solo formatea esos datos en un documento por capa;
no infiere ni inventa. Ejecutar:  python -m scripts.docs.gen_capas
"""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DEST = RAIZ / "docs" / "CAPAS"

# Cada capa: campos verificados contra el código.
CAPAS: list[dict] = [
    dict(n=0, nombre="Captura e Ingesta",
         objetivo="Traer señales públicas crudas de fuentes externas.",
         problema="La evidencia vive dispersa en prensa, feeds y job boards; hay que capturarla sin interpretarla.",
         arquitectura="Conectores intercambiables (search/fetch/normalize/validate) + ingesta gratuita (RSS/YouTube) que emite al webhook.",
         componentes="hd_scraper/connectors/{base,google_news,gdelt,rss_fijos,job_boards}.py, hd_scraper/ingesta/{noticias,youtube,webhook}.py, hd_scraper/signals.py",
         endpoints="POST /webhook/ingesta, POST /ingesta/noticias, GET /senales-capa0",
         tablas="senales_capa0",
         funciones="connector.search/fetch/normalize, detectar_keywords, calcular_confianza, fuente_confiable",
         entradas="QuerySpec (empresa, tipo_evento, categoría)",
         salidas="RawItem crudos + señales Capa 0",
         dependencias="→ Capa 1 (Normalización)",
         tests="test_google_news, test_gdelt, test_rss_fijos, test_job_boards, test_ingesta_connectors, test_signals",
         criterios="Un 404 de job board = 'slug no está', no cuenta como fallo; salud por sub-fuente.",
         limitaciones="El proxy de egress puede bloquear news.google.com / api.gdeltproject.org.",
         relacion="Alimenta a C1/C2; salud gestionada por governance/."),
    dict(n=1, nombre="Normalización",
         objetivo="Normalizar URL/empresa/título y calcular hashes de deduplicación.",
         problema="La misma noticia aparece con URLs y títulos distintos; hay que dedup de forma estable.",
         arquitectura="Funciones puras de normalización + hashes (sha256).",
         componentes="hd_scraper/db/models.py, hd_scraper/pipeline.py",
         endpoints="(sin endpoint propio; interno del pipeline)",
         tablas="(prepara filas para evidencias)",
         funciones="normalizar_url, normalizar_empresa, normalizar_titulo, hash_contenido, clave_contenido, calcular_hash_dedup",
         entradas="RawItem crudo",
         salidas="EvidenceRecord normalizado con hash_dedup",
         dependencias="← C0 · → C2",
         tests="test_models",
         criterios="hash_dedup = sha256(empresa + URL normalizada), único.",
         limitaciones="La detección de duplicados depende de la normalización de título.",
         relacion="Puente entre captura (C0) y contrato de evidencia (C2)."),
    dict(n=2, nombre="Evidencia (contrato)",
         objetivo="Guardián único del contrato de la tabla evidencias.",
         problema="Solo debe persistirse evidencia completa y trazable; lo incompleto no puede contaminar el corpus.",
         arquitectura="Validador único; registro incompleto → rechazos; sin fecha → estado no_fechado.",
         componentes="hd_scraper/validation/validator.py, hd_scraper/db/models.py",
         endpoints="GET /evidencias, GET /evidencias/{id}, GET /corpus",
         tablas="evidencias, rechazos",
         funciones="validate (contrato), campos_contrato, _row_a_corpus",
         entradas="EvidenceRecord",
         salidas="Fila en evidencias (estado ok|no_fechado) o rechazo",
         dependencias="← C1 · → C3, corpus para Motor B",
         tests="test_validator, test_corpus, test_scrape, test_intake",
         criterios="Obligatorios: cita_textual, fecha_extraccion, url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup.",
         limitaciones="no_fechado no es consumible por la API (pero no se rechaza).",
         relacion="Fuente del corpus (contrato motor_a.corpus.v1) que consume RadarHD."),
    dict(n=3, nombre="Inferencia Antropológica",
         objetivo="Convertir señales objetivas en análisis profundo DETERMINISTA (sin IA).",
         problema="Hace falta clasificar (scoring, Dolor Cultural, ICP) de forma reproducible y auditable.",
         arquitectura="Reglas y tablas declaradas; combinaciones de señales; profundidad × vertical.",
         componentes="hd_scraper/analisis.py, hd_scraper/engine/rule_engine.py, hd_scraper/dictamen.py",
         endpoints="POST /analizar, GET /alertas",
         tablas="(opera sobre evidencias agregadas)",
         funciones="analizar, _deuda_principal, _senal_dominante, _intensidad, _calcular_profundidad, generar_dictamen, generar_ranking",
         entradas="keywords, vertical, confianza, calidad",
         salidas="scoring A/B/C, tipo_deuda, score_icp, profundidad_dolor, viabilidad, decisor, razon",
         dependencias="← C2 · → C9, C10, C11",
         tests="test_analisis, test_rule_engine, test_fase2",
         criterios="Mismo insumo ⇒ mismo resultado. Sin LLM. Interpretación declarada (Frontera de Interpretación).",
         limitaciones="Hipótesis preliminares; la validación de rigor la hace C11.",
         relacion="Único motor de inferencia del ecosistema (ADR-0001)."),
    dict(n=4, nombre="Relevancia y Señales",
         objetivo="Filtrar ruido, detectar el sujeto (empresa) y medir calidad de captura.",
         problema="No toda noticia es relevante ni menciona una organización objetivo.",
         arquitectura="Reglas de relevancia + detección de nombre propio + keywords de señal.",
         componentes="hd_scraper/relevance.py, hd_scraper/signals.py",
         endpoints="(interno; usado por pipeline y expedientes)",
         tablas="(anota confianza/calidad en evidencias)",
         funciones="detectar_empresa, es_opinion, evaluar_relevancia, calcular_calidad, detectar_keywords, calcular_confianza",
         entradas="Título/cita textual",
         salidas="Relevancia (bool), empresa detectada, keywords, confianza, calidad",
         dependencias="← C0/C2 · → C3",
         tests="test_relevance, test_signals",
         criterios="Subcadena sin acentos = extracción (no interpretación).",
         limitaciones="Detección de empresa por heurística de nombre propio.",
         relacion="Habilita la agregación de expedientes y el scoring de C3."),
    dict(n=5, nombre="Enriquecimiento",
         objetivo="Resolver sitio oficial, discurso corporativo, vertical y contacto.",
         problema="La evidencia gana valor con contexto (web oficial, tesis, decisor).",
         arquitectura="Resolución multi-estrategia con niveles de confianza; Wikidata con caché.",
         componentes="hd_scraper/enrich.py, hd_scraper/contacto.py, hd_scraper/directorio.py, hd_scraper/hunter.py",
         endpoints="POST /enrich, POST /verificar-contacto, POST /directorio",
         tablas="directorio_cache",
         funciones="resolver_sitio, extraer_discurso, sugerir_vertical, enriquecer, rutas_contacto, dominio_de",
         entradas="Nombre de la entidad",
         salidas="Sitio (candidato con confianza), discurso, vertical, enlaces, contacto",
         dependencias="← C4 · → C10",
         tests="test_enrich, test_contacto, test_directorio, test_hunter",
         criterios="El sitio es un CANDIDATO con nivel de confianza; LinkedIn no se raspa (solo enlace).",
         limitaciones="Hunter es opcional (requiere HUNTER_API_KEY).",
         relacion="Aporta 'thick data' a prospectos y a la curaduría."),
    dict(n=6, nombre="Drift Narrativo",
         objetivo="Detectar cambios en el discurso público entre snapshots.",
         problema="El relato de una organización cambia con el tiempo; ese cambio es evidencia.",
         arquitectura="Snapshots versionados; comparación de consecutivos → evidencias narrativas (hechos).",
         componentes="hd_scraper/drift.py, hd_scraper/drift_compare.py",
         endpoints="POST /drift/capturar, GET /drift/{org}",
         tablas="drift_snapshots, drift_evidencias",
         funciones="capturar_snapshot, obtener_timeline, obtener_snapshot_anterior",
         entradas="org_nombre, sitio_web",
         salidas="Timeline de snapshots + evidencias de cambio (tipo cerrado)",
         dependencias="← C5 · → C9",
         tests="test_drift, test_drift_compare",
         criterios="Los tipos de cambio están cerrados; se observa el hecho, no se interpreta.",
         limitaciones="Requiere páginas observables (no SPA/robots/bloqueo).",
         relacion="Nutre el DolorMap (C9) con evolución del relato."),
    dict(n=7, nombre="Onlife",
         objetivo="Observar señales conductuales en espacios digitales.",
         problema="La vida operativa de una organización deja rastro fuera de la prensa.",
         arquitectura="Observadores por fuente (GitHub, Hacker News, blog/changelog) → señales estructuradas.",
         componentes="hd_scraper/onlife.py",
         endpoints="POST /onlife/observar, GET /onlife/{org}",
         tablas="onlife_signals",
         funciones="observar, observar_github, observar_hackernews, observar_blog, persistir_señales, obtener_perfil",
         entradas="org_nombre (+ fuentes)",
         salidas="Señales onlife por fuente + perfil consolidado",
         dependencias="← C5 · → C9",
         tests="test_onlife",
         criterios="Determinista sobre lo observado; dedup por hash.",
         limitaciones="Depende de disponibilidad de las fuentes públicas.",
         relacion="Aporta comportamiento al DolorMap (C9)."),
    dict(n=8, nombre="Pipeline Comercial",
         objetivo="Modelar etapas del embudo por organización.",
         problema="Se necesita registrar el estado de seguimiento de una organización.",
         arquitectura="Etapas + transiciones; dedup por hash de org.",
         componentes="hd_scraper/pipeline_comercial.py",
         endpoints="POST /pipeline/registrar, POST /pipeline/avanzar, GET /pipeline, GET /pipeline/funnel, GET /pipeline/{org}",
         tablas="pipeline_comercial, pipeline_transiciones",
         funciones="registrar_org, avanzar, obtener_pipeline, listar_pipeline, resumen_funnel",
         entradas="org_nombre, etapa",
         salidas="Estado del embudo + transiciones + funnel",
         dependencias="← C9",
         tests="test_pipeline_comercial",
         criterios="Modela y persiste estado; NO ejecuta contacto (sin envío de emails).",
         limitaciones="VESTIGIAL: el pipeline comercial real y ejecutado vive en RadarHD (Motor C). A deprecar (ADR-0001 / ROADMAP).",
         relacion="Cruza la frontera con Motor C; ver docs/FRONTERAS_MOTORES.md y INCONSISTENCIAS.md."),
    dict(n=9, nombre="Dolor Cultural / DolorMap",
         objetivo="Vista consolidada por organización (todas las capas).",
         problema="La inteligencia por org está repartida entre evidencia, drift, onlife y análisis.",
         arquitectura="Agregación por organización + análisis determinista + patrones.",
         componentes="hd_scraper/analisis.py + endpoints en api/app.py (dolormap, dossier)",
         endpoints="GET /dolormap/{org}, GET /dossier/{org}",
         tablas="(lee evidencias, drift, onlife, pipeline)",
         funciones="_detectar_patrones, _construir_expedientes, dolormap, dossier_org",
         entradas="org_nombre",
         salidas="Expediente consolidado + dossier HTML imprimible",
         dependencias="← C3, C6, C7, C8 · → C10, C11, C12",
         tests="test_dolormap",
         criterios="Hipótesis marcadas como preliminares hasta validación (C11).",
         limitaciones="El dossier se sirve como HTML (brecha JSON para Motor B, ROADMAP).",
         relacion="Insumo del expediente que validan/gobiernan C11/C12."),
    dict(n=10, nombre="Curaduría Antropológica",
         objetivo="Transformar expedientes en una lectura de ecosistema (conclusiones primero).",
         problema="El usuario necesita significado, no una lista de hechos.",
         arquitectura="Tensión central por umbrales + narrativa determinista + convergencias.",
         componentes="hd_scraper/curaduria.py, hd_scraper/dictamen.py",
         endpoints="POST /investigacion, GET /centro, GET /informe(.md/.csv), GET /informes",
         tablas="informes_guardados",
         funciones="curar, _identificar_tension, _construir_narrativa, _curar_convergencias, _organizaciones_curadas",
         entradas="Lista de expedientes (+ query/region/vertical)",
         salidas="Tensión, narrativa, convergencias, preguntas abiertas, siguiente paso",
         dependencias="← C9 · → C11",
         tests="test_curaduria, test_centro_corpus, test_informe, test_export",
         criterios="100% determinista; no juzga (contradicciones/vacíos los trata C11).",
         limitaciones="Sin datos, entrega curaduría 'sin evidencia suficiente'.",
         relacion="Capa que precede a la Validación Científica (C11)."),
    dict(n=11, nombre="Validación Científica",
         objetivo="Auditar la calidad epistémica de cada hipótesis y emitir el Dictamen Científico.",
         problema="Una hipótesis sin evidencia suficiente no debe sostenerse ni escalar.",
         arquitectura="14 funciones puras; umbrales declarados; bloqueo automático.",
         componentes="hd_scraper/validacion_cientifica.py",
         endpoints="GET /validacion/{org}",
         tablas="(opera sobre el expediente en memoria)",
         funciones="14: contar_fuentes_independientes, calcular_confianza_agregada, validar_trazabilidad, validar_fechado, calcular_suficiencia_corpus, calcular_solidez, detectar_contradicciones, detectar_vacios, validar_reproducibilidad, nivel_evidencia, evaluar_bloqueo_hipotesis, clasificar_veredicto, emitir_dictamen_cientifico, validar_expediente",
         entradas="Expediente (hipótesis + evidencia)",
         salidas="Veredicto (VALIDADA|VALIDADA_PARCIAL|NO_VALIDADA|BLOQUEADA|SIN_HIPOTESIS), solidez, suficiencia, nivel GRADE",
         dependencias="← C10 · → C12",
         tests="test_validacion_cientifica (46), 100% cobertura",
         criterios="MIN_EVIDENCIAS=3, MIN_FUENTES_INDEPENDIENTES=2; bloqueo si bajo umbral.",
         limitaciones="No re-extrae evidencia; audita la ya producida.",
         relacion="Integrada en _construir_expedientes (bloqueo automático); insumo de C12."),
    dict(n=12, nombre="Gobernanza Científica",
         objetivo="Hacer toda conclusión auditable, reproducible y explicable.",
         problema="Sin versionado/huella/certificado, una conclusión no es reconstruible.",
         arquitectura="14 funciones puras + persistencia idempotente; fecha fuera del hash.",
         componentes="hd_scraper/gobernanza.py, hd_scraper/gobernanza_store.py",
         endpoints="GET /auditoria/{org}, GET /certificado/{org}",
         tablas="versionado_modelo, huellas_digitales, bitacora_decisiones, auditoria_expedientes, certificados",
         funciones="registrar_version_{modelo,taxonomia,corpus,pipeline,expediente}, generar_huella_digital, validar_integridad, verificar_consistencia, comparar_versiones, construir_linea_tiempo, registrar_decision, generar_bitacora, firmar_motor, emitir_certificado, auditar_expediente",
         entradas="Expediente + validación",
         salidas="Huella, certificado con firma del Motor, bitácora, auditoría",
         dependencias="← C11 · → C13",
         tests="test_gobernanza (34), 100% cobertura",
         criterios="Mismo insumo ⇒ misma huella/firma (fecha es metadato).",
         limitaciones="Firma = sha256 determinista (no criptografía de clave pública).",
         relacion="Sella cada expediente; base de la Memoria (C13). Ver ADR/ADR_0003_GOBERNANZA.md."),
    dict(n=13, nombre="Memoria Científica",
         objetivo="Historial longitudinal inmutable de cada expediente.",
         problema="El conocimiento evoluciona; hay que conservar todas las versiones sin sobrescribir.",
         arquitectura="Append-only; version_num monótono; dedup por hash de huella.",
         componentes="hd_scraper/memoria.py, hd_scraper/memoria_store.py",
         endpoints="GET /historial/{org}, GET /timeline/{org}, GET /versiones/{org}",
         tablas="memoria_cientifica (UNIQUE org_nombre, version_num)",
         funciones="crear_version, comparar_versiones, detectar_cambios, construir_timeline, calcular_evolucion, emitir_historial, guardar_version, recuperar_historial",
         entradas="Expediente + validación + huella",
         salidas="Timeline científica, evolución del dolor, comparación de versiones",
         dependencias="← C12 · → C14",
         tests="test_memoria (17), 100% cobertura",
         criterios="Nunca UPDATE/DELETE; solo añade si el estado cambió.",
         limitaciones="La versión se registra al llamar /auditoria (idempotente).",
         relacion="Base del comparador (C14) y el predictivo (C15)."),
    dict(n=14, nombre="Comparador Temporal y Ecosistémico",
         objetivo="Comparar organizaciones, ecosistemas, periodos y patrones.",
         problema="Se necesita contraste estructural sin interpretación.",
         arquitectura="Funciones puras de diferencia (sets, distribuciones).",
         componentes="hd_scraper/comparador.py",
         endpoints="GET /comparar, GET /ecosistema/comparar, GET /periodos",
         tablas="(opera sobre expedientes)",
         funciones="comparar_organizaciones/ecosistemas/periodos/patrones/narrativas/dolor/validaciones, detectar_convergencias/divergencias, generar_matriz",
         entradas="Dos organizaciones/conjuntos o una org + fecha de corte",
         salidas="Diferencias campo a campo, matriz, convergencias/divergencias",
         dependencias="← C13 · → C16, C18",
         tests="test_comparador (15), 100% cobertura",
         criterios="Solo compara, no interpreta.",
         limitaciones="Comparación de narrativas por solapamiento léxico (Jaccard).",
         relacion="Alimenta al Observatorio (C16)."),
    dict(n=15, nombre="Motor Predictivo Antropológico",
         objetivo="Detectar trayectorias culturales con reglas deterministas.",
         problema="Anticipar sin IA ni modelos opacos, solo con evidencia histórica.",
         arquitectura="Serie temporal mensual + mínimos cuadrados + banda de volatilidad.",
         componentes="hd_scraper/predictivo.py",
         endpoints="GET /proyeccion/{org}, GET /escenarios/{org}",
         tablas="(deriva serie de evidencias fechadas)",
         funciones="serie_temporal, calcular_tendencia/estabilidad/volatilidad/madurez, proyectar_escenarios, estimar_riesgo, detectar_inflexiones, emitir_proyeccion",
         entradas="Expediente (evidencia histórica)",
         salidas="Tendencia, estabilidad, volatilidad, escenarios, riesgo, madurez, inflexiones",
         dependencias="← C13 · → C18",
         tests="test_predictivo (23), 100% cobertura",
         criterios="Proyección aritmética declarada; sin aleatoriedad ni IA.",
         limitaciones="No es predicción probabilística; requiere serie con historia.",
         relacion="Complementa el Observatorio y el Sistema Operativo."),
    dict(n=16, nombre="Observatorio LATAM",
         objetivo="Pasar de la organización individual al ecosistema.",
         problema="Se necesita inteligencia agregada por región/vertical/ecosistema.",
         arquitectura="Agregación determinista; reutiliza ranking (C3) y riesgo (C15).",
         componentes="hd_scraper/observatorio.py",
         endpoints="GET /latam, GET /latam/{pais}, GET /vertical/{nombre}",
         tablas="(opera sobre expedientes)",
         funciones="analizar_region/vertical/ecosistema, identificar_patrones_regionales/tensiones, calcular_indicadores, emitir_reporte_regional",
         entradas="Conjunto de expedientes (+ filtro país/vertical)",
         salidas="Ranking, riesgos comunes, patrones, vacíos sistémicos, tensiones, indicadores",
         dependencias="← C3, C14, C15 · → C18",
         tests="test_observatorio (13), 100% cobertura",
         criterios="País por mención literal (substring sin acentos) = extracción.",
         limitaciones="Algunas vistas avanzadas (clusters/outliers) no tienen endpoint aún.",
         relacion="Fuente ecosistémica del dashboard (C18)."),
    dict(n=17, nombre="Publicador Científico",
         objetivo="Generar documentación científica desde evidencia validada.",
         problema="Hay que producir peritajes/informes firmados y reproducibles.",
         arquitectura="Builders puros JSON/CSV/HTML/PDF + firma determinista.",
         componentes="hd_scraper/publicador.py",
         endpoints="GET /publicar/peritaje/{org} (json|csv|html), GET /publicar/informe/{org}, GET /publicar/pdf/{org}",
         tablas="(usa expediente + validación + gobernanza)",
         funciones="generar_peritaje/informe/pdf/html/json/csv, firmar_documento",
         entradas="Expediente + validación + huella + certificado",
         salidas="Documento firmado; publicable=False si el veredicto no valida",
         dependencias="← C11, C12 · reutiliza C3 (dictamen)",
         tests="test_publicador (13), 100% cobertura",
         criterios="Nunca inventa; la firma cubre el contenido científico (no la fecha).",
         limitaciones="El 'PDF' es HTML imprimible (convención del repo).",
         relacion="Consume la ciencia de C11/C12 para exportarla."),
    dict(n=18, nombre="Sistema Operativo del Laboratorio",
         objetivo="Integrar las 19 capas en un dashboard maestro y estado integral.",
         problema="Se necesita una vista única del estado de motores, corpus, ciencia y gobernanza.",
         arquitectura="Funciones puras que agregan estados ya calculados; endpoint HTML.",
         componentes="hd_scraper/laboratorio.py",
         endpoints="GET /laboratorio, GET /estado, GET /dashboard (HTML)",
         tablas="(lee conteos de todas las tablas)",
         funciones="estado_general/capas/corpus/pipeline/validacion/gobernanza/observatorio",
         entradas="Conteos de BD + expedientes",
         salidas="Estado integral (motores A/B/C, corpus, validación, gobernanza, 19 capas)",
         dependencias="← C11, C12, C16 (y conteos de todas)",
         tests="test_laboratorio (13), 100% cobertura",
         criterios="Determinista; el dashboard HTML es bien formado (verificado).",
         limitaciones="Los estados de Motor B/C son declarativos (viven en RadarHD).",
         relacion="Capa cúspide: consolida el estado del pipeline completo."),
]

PLANTILLA = """# Capa {n:02d} — {nombre}

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** {objetivo}
- **Problema que resuelve:** {problema}
- **Arquitectura:** {arquitectura}

## Componentes (archivos)
{componentes}

## Endpoints
{endpoints}

## Tablas
{tablas}

## Funciones
{funciones}

## Entradas → Salidas
- **Entradas:** {entradas}
- **Salidas:** {salidas}

## Dependencias
{dependencias}

## Tests
{tests}

## Criterios de aceptación
{criterios}

## Limitaciones
{limitaciones}

## Relación con otras capas
{relacion}
"""


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for c in CAPAS:
        destino = DEST / f"CAPA_{c['n']:02d}.md"
        destino.write_text(PLANTILLA.format(**c), encoding="utf-8")
    print(f"Generadas {len(CAPAS)} capas en {DEST}")


if __name__ == "__main__":
    main()
