"""Captura Inteligente: filtro de relevancia y calidad — 100% objetivo.

Este módulo reduce el ruido del corpus SIN convertir al Motor A en un
clasificador. Todas las decisiones son deterministas, documentadas y basadas en
ESTRUCTURA (mayúsculas, presencia de palabras clave de señal, marcadores léxicos
de opinión, fuente nombrada). No hay IA ni juicio semántico: eso sigue siendo
responsabilidad exclusiva del Motor B (RadarHD).

Dos responsabilidades:

1) ``evaluar_relevancia`` — decide si un titular de descubrimiento merece entrar
   al corpus. Descarta, con motivo auditable, lo que el operador pidió filtrar:
     - artículos de opinión / columnas / editoriales / listículos / tendencias,
     - análisis general de industria sin empresa,
     - noticias que no mencionan una empresa concreta,
     - noticias que no describen un evento de negocio verificable.

2) ``calcular_calidad`` — etiqueta INFORMATIVA (Alta | Media | Baja) calculada a
   partir de criterios objetivos. Es puramente descriptiva del acto de captura;
   NO modifica el scoring del Motor B ni el contrato ``motor_a.corpus.v1``.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

# ── Normalización auxiliar ───────────────────────────────────────────────────

def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm(texto: str) -> str:
    return _sin_acentos((texto or "").lower())


# Google News añade " - Medio" al final del titular; ese sufijo NO es contenido
# ni una empresa. Se recorta antes de detectar el nombre propio.
_RE_MEDIO = re.compile(r"\s+[-–|]\s+[^-–|]+$")


def _sin_medio(titulo: str) -> str:
    t = (titulo or "").strip()
    recortado = _RE_MEDIO.sub("", t).strip()
    return recortado or t


# Simétrico a ``_RE_MEDIO`` pero al INICIO: algunos medios anteponen una
# etiqueta de sección separada por "|" ("Primicia | Plataforma Tul anuncia...").
# Solo el separador "|" (nunca ":") porque los dos puntos son parte normal de
# un titular en español con subtítulo propio ("Santander México:
# Transformación Digital..." — ahí "Santander México" SÍ es contenido, no una
# etiqueta desechable; usar ":" como señal habría recortado la empresa real).
# El "|" wire-service SÍ es una convención de etiqueta desechable, no de
# subtítulo. Caso real (auditoría 2026-09-14): "Primicia | Plataforma Tul
# anuncia recorte..." detectaba "Primicia" en vez de "Tul".
_RE_PREFIJO_SECCION = re.compile(
    r"^[A-ZÁÉÍÓÚÑÜ][\wÁÉÍÓÚÑÜáéíóúñü]*(?:\s+[A-ZÁÉÍÓÚÑÜa-záéíóúñü]+)?\s*\|\s+"
)


def _sin_prefijo_seccion(titulo: str) -> str:
    t = (titulo or "").strip()
    recortado = _RE_PREFIJO_SECCION.sub("", t).strip()
    return recortado or t


# Sufijos de futuro simple en español, 3ª persona singular/plural de verbos
# regulares -ar/-er/-ir ("condonará"/"condonarán", "venderá"/"venderán",
# "invertirá"/"invertirán"...), sobre el token YA sin acentos y en minúsculas
# (mismo ``base`` que ya calcula el bucle de abajo: "-ará" y "-ara" son
# indistinguibles sin acento, y da igual — ambas son formas verbales, nunca
# un nombre propio). Un verbo conjugado que encabeza un titular en orden
# invertido queda capitalizado SOLO por ir al inicio de la oración, no es un
# nombre propio. A diferencia de la lista de verbos en presente de
# ``_STOP_CAP`` (cerrada, un verbo por incidente confirmado), este es un
# patrón MORFOLÓGICO: cubre cualquier verbo regular en ese tiempo sin
# enumerarlo, porque el sufijo es productivo en español y una empresa real no
# termina en él. Caso real (auditoría 2026-09-14): "Condonarán deuda a
# productores rurales..." detectaba "Condonarán" como organización.
_RE_SUFIJO_FUTURO = re.compile(r"(?:ar|er|ir)an?$")


def _parece_verbo_conjugado(base: str) -> bool:
    """¿``base`` (ya sin acentos, en minúsculas) termina en un sufijo de
    futuro simple español? Longitud mínima para no descartar nombres propios
    cortos por coincidencia accidental de las últimas letras."""
    return len(base) >= 6 and bool(_RE_SUFIJO_FUTURO.search(base))


# Sufijo nominalizador "-aje": productivo en español para sustantivos comunes
# de acción/colectivo formados sobre un verbo o una raíz ("reciclar" ->
# "reciclaje", "aprender" -> "aprendizaje", "hospedar" -> "hospedaje").
# Igual que ``_RE_SUFIJO_FUTURO``, es un patrón MORFOLÓGICO (no una lista de
# palabras): ninguna empresa real usa este sufijo como nombre propio, así que
# un token que lo lleva y va capitalizado solo por abrir la oración no es una
# organización. Caso real (auditoría 2026-09-14): "Reciclaje de baterías...
# en Redwood Materials" detectaba "Reciclaje" en vez de "Redwood Materials".
_RE_SUFIJO_SUSTANTIVO_COMUN = re.compile(r"aje$")


def _parece_sustantivo_comun(base: str) -> bool:
    """¿``base`` (ya sin acentos, en minúsculas) termina en un sufijo
    nominalizador español productivo de sustantivo común? Longitud mínima
    para no descartar siglas o nombres propios cortos por coincidencia."""
    return len(base) >= 5 and bool(_RE_SUFIJO_SUSTANTIVO_COMUN.search(base))


# ── Detección de empresa (objetiva, sin IA) ──────────────────────────────────
#
# Heurística estructural: una empresa aparece como NOMBRE PROPIO en el titular.
# Buscamos tokens que empiezan en mayúscula (o siglas en mayúsculas) y cuya forma
# en minúsculas NO es una palabra común española ni un término genérico de
# sector. Es una señal de "hay una entidad nombrada", no una identificación
# semántica. Documentada y determinista.

# Palabras que suelen ir capitalizadas al inicio de frase o son genéricas: NO son
# nombres de empresa por sí solas.
_STOP_CAP = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "este", "esta",
    "estos", "estas", "ese", "esa", "su", "sus", "al", "del", "y", "o", "e", "u",
    "en", "con", "por", "para", "como", "cuando", "donde", "que", "quien", "cual",
    "cuanto", "cuanta", "cuantos", "cuantas", "porque", "segun", "tras", "sobre",
    "ante", "hasta", "desde", "entre", "sin", "mientras", "aunque", "asi",
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
    "septiembre", "setiembre", "octubre", "noviembre", "diciembre",
    "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
    "mexico", "colombia", "chile", "peru", "argentina", "brasil", "brazil",
    "panama", "latam", "latinoamerica", "america", "espana",
    "nuevo", "nueva", "nuevos", "nuevas", "mas", "menos", "gran", "gobierno",
    "estado", "pais",
    # Incidente real 2026-09-10: "Lana" (palabra común, no nombre de empresa)
    # detectada como organización en un titular.
    "lana",
    # Incidente real 2026-09-12: "Despido"/"Demanda" (sustantivos comunes en
    # español, no nombres propios) detectados como organización en /expedientes
    # — mismo patrón que "Lana", vocabulario propio de las señales de negocio
    # (signals.py: reduccion_personal, friccion_retencion) que aparece
    # capitalizado al inicio de titular en orden invertido.
    "despido", "despidos", "demanda", "demandas",
    # Incidente real 2026-09-12: "Fideicomiso" (sustantivo institucional
    # común, no nombre de empresa) detectado como organización — mismo
    # patrón que "Lana"/"Despido"/"Demanda".
    "fideicomiso",
    # Auditoría 2026-09-11 (hallazgo ALTO): verbos conjugados en 3ª persona
    # que encabezan titulares en orden invertido verbo-sujeto ("Cierra Konfío
    # tercera adquisición"). Capitalizados solo por ir al inicio de la
    # oración, no son nombres propios. Lista cerrada, incident-driven: no
    # pretende cubrir todo verbo posible, solo los ya observados en el
    # corpus real de titulares de negocio en español.
    "cierra", "anuncia", "lanza", "compra", "vende", "despide", "recorta",
    "adquiere", "firma", "presenta", "confirma", "niega", "revela", "gana",
    "pierde", "crece", "cae", "sube", "baja", "abre", "renuncia", "nombra",
    "designa", "reporta", "invierte", "levanta", "recauda", "cierran",
}

# Nombres de pila comunes en español (LATAM/México) que NO deben promoverse a
# organización cuando aparecen como el primer candidato capitalizado de un
# titular (p. ej. "Ana Ríos, CEO de Kavak..." o "...nuevo CEO: Armando
# Herrera"). Auditoría 2026-09-11 (hallazgo ALTO), reproducido con evidencia
# real del flujo de escritura/clasificación/promoción.
#
# Lista cerrada y DELIBERADAMENTE INCOMPLETA (no existe un léxico exhaustivo
# de nombres de pila): reduce el riesgo, no lo elimina. Cubre los casos ya
# auditados más un conjunto acotado de nombres frecuentes en bylines de
# prensa de negocios en español. Ver CLAUDE.md "Errores recurrentes" para el
# criterio de cuándo ampliar una lista cerrada por incidente.
_NOMBRES_PROPIOS_PERSONA = {
    "ana", "sofia", "armando", "juan", "maria", "jose", "luis", "carlos",
    "miguel", "jorge", "fernando", "alejandro", "ricardo", "roberto",
    "eduardo", "francisco", "antonio", "manuel", "pedro", "rafael",
    "sergio", "diego", "andres", "pablo", "daniel", "david", "gabriel",
    "adriana", "alejandra", "alicia", "carmen", "claudia", "cristina",
    "elena", "fernanda", "gabriela", "isabel", "laura", "lucia",
    "mariana", "marisol", "patricia", "paula", "paulina", "rosa",
    "silvia", "valentina", "valeria", "veronica", "ximena",
}

# Términos genéricos de sector: describen el rubro, no a la empresa.
_GENERICOS_SECTOR = {
    "fintech", "edtech", "healthtech", "agtech", "insurtech", "proptech",
    "startup", "startups", "scaleup", "scaleups", "unicornio", "unicornios",
    "empresa", "empresas", "compania", "companias", "firma", "banco", "bancos",
    "plataforma", "app", "aplicacion", "mercado", "sector", "industria",
    "tecnologia", "digital", "ronda", "serie",
    # Auditoría 2026-09-11: "Grupo"/"Galería" solas (sin nombre propio
    # pegado) son clasificadores genéricos, no una empresa — mismo patrón ya
    # establecido para "banco" ("Banco Santander" -> se descarta "Banco" y se
    # detecta "Santander"; "Grupo Bimbo" -> se descarta "Grupo" y se detecta
    # "Bimbo").
    "grupo", "galeria",
}

# Sufijos de forma jurídica/corporativa: acompañan al nombre real de una
# empresa ("Acme Corp", "Acme Inc", "Acme S.A.") pero no son parte de la
# identidad distintiva de la organización — mismo patrón estructural que
# "banco"/"grupo" en ``_GENERICOS_SECTOR`` (un clasificador institucional
# genérico, no la empresa), aplicado aquí a la extensión de un candidato ya
# encontrado: no debe fundirse "Acme" con "Corp" en un solo nombre "Acme
# Corp" cuando el sufijo es puramente la forma jurídica. Lista cerrada de
# abreviaturas de forma jurídica realmente usadas en LATAM/EE.UU., no de
# nombres de empresa.
_SUFIJOS_CORPORATIVOS = {
    "corp", "inc", "ltd", "llc", "plc", "srl", "sa", "sab", "sapi", "sas",
    "co",
}

# Siglas que NUNCA son empresa: cargos ejecutivos y organismos de gobierno/
# regulación. detectar_empresa() las trata como _es_sigla() por forma (todo
# mayúsculas), pero no son una entidad nombrada — son un rol o un regulador.
# Incidente real 2026-09-10: "CEO de Kavak regresa..." detectó "CEO"; "CNBV
# multa a la fintech Albo..." detectó "CNBV" (el regulador bancario de
# México, no una empresa), con ICP 79 y 99 respectivamente.
_SIGLAS_NO_EMPRESA = {
    "ceo", "cfo", "cto", "coo", "cmo", "cpo", "chro", "cio", "cro",
    "cnbv", "sat", "imss", "infonavit", "inegi", "profeco", "condusef",
    "banxico", "shcp", "sec", "irs", "ftc",
    "ong", "pyme", "pymes", "ia", "roi", "kpi", "kpis",
}


def _es_sigla(token: str) -> bool:
    """Sigla tipo BBVA, IBM, SAP: 2+ letras todas mayúsculas."""
    return len(token) >= 2 and token.isupper() and token.isalpha()


# Desambiguación política estricta (incidente real 2026-09-12): "Clara" es
# simultáneamente una fintech real y el nombre de pila de una figura política
# vigente ("Clara Brugada"). A diferencia de _NOMBRES_PROPIOS_PERSONA (que
# descarta el nombre SIEMPRE, sin importar contexto), esta lista solo se
# activa cuando el nombre ambiguo está seguido INMEDIATAMENTE por uno de sus
# apellidos políticos documentados — "Clara" sola, o "Clara" junto a
# marcadores de ecosistema ("fintech", "levanta", "capital", "serie"...),
# sigue reconociéndose como empresa (ver
# test_detectar_empresa_ignora_articulo_inicial_y_sector). Lista cerrada,
# incident-driven: se amplía solo ante un caso real confirmado, igual que
# _STOP_CAP.
_APELLIDOS_POLITICOS_AMBIGUOS: dict[str, set[str]] = {
    "clara": {"brugada"},
}


def _token_extiende_candidato(token_texto: str) -> bool:
    """¿Puede este token CONTINUAR un candidato de empresa ya iniciado?

    Versión ligera del filtro principal, sin el manejo de estado
    (apellido/ambigüedad política) que solo aplica al primer token de un
    candidato: un token de continuación válido es capitalizado o sigla, no
    es palabra común/término de sector/sigla-no-empresa/sufijo de forma
    jurídica (evita fundir "Acme" con "Corp" en "Acme Corp" — caso real:
    ``test_api_materializar_y_listar`` esperaba "Acme" desde "Acme Corp
    enfrenta fricción"), no es un nombre de pila (evita fundir "Redwood" con
    el apellido de una persona citada más adelante) y no parece un verbo
    conjugado.
    """
    limpio = token_texto.strip()
    if len(limpio) < 3 and not _es_sigla(limpio):
        return False
    base = _sin_acentos(limpio).lower()
    if (
        base in _STOP_CAP
        or base in _GENERICOS_SECTOR
        or base in _SIGLAS_NO_EMPRESA
        or base in _SUFIJOS_CORPORATIVOS
    ):
        return False
    if base in _NOMBRES_PROPIOS_PERSONA:
        return False
    if not (limpio[0].isupper() or _es_sigla(limpio)):
        return False
    if _parece_verbo_conjugado(base):
        return False
    return not _parece_sustantivo_comun(base)


def detectar_empresa(titulo: str) -> Optional[str]:
    """Devuelve un candidato a empresa nombrada en el titular, o ``None``.

    Objetivo (sin IA): recorre los tokens y devuelve el que parezca nombre
    propio (mayúscula inicial o sigla) y no sea palabra común ni término de
    sector. No garantiza que sea "la" empresa; garantiza que HAY una entidad
    nombrada, que es la condición objetiva pedida.

    Conservador por diseño (auditoría 2026-09-11, hallazgo ALTO): ante duda
    entre "es una organización" y "es una persona/un verbo", se descarta y se
    sigue buscando, nunca se inventa una organización. Mecanismos, todos sobre
    listas cerradas o patrones morfológicos ya existentes en el módulo:

    1. Un nombre de pila conocido (``_NOMBRES_PROPIOS_PERSONA``) nunca se
       devuelve como organización.
    2. El token INMEDIATAMENTE contiguo (solo espacio de por medio) al que
       acaba de descartarse por ser un nombre de pila se trata como su
       apellido y tampoco se devuelve — evita que "Ana Ríos" o "Armando
       Herrera" terminen devolviendo la mitad del nombre de una persona.
    3. Desambiguación política estricta (``_APELLIDOS_POLITICOS_AMBIGUOS``):
       un nombre ambiguo entre fintech real y figura política solo se
       descarta (junto a su apellido contiguo) cuando el apellido político
       documentado aparece pegado — "Clara Brugada" se descarta, "Clara"
       sola o con marcadores de ecosistema no.
    4. Un verbo conjugado en futuro simple que encabeza un titular en orden
       invertido ("Condonarán deuda a...") se descarta por su SUFIJO
       morfológico (``_parece_verbo_conjugado``), no por estar en una lista.
    5. Un sustantivo común formado con el sufijo nominalizador "-aje"
       ("Reciclaje de baterías...") se descarta por su SUFIJO morfológico
       (``_parece_sustantivo_comun``), tampoco por estar en una lista.

    Devuelve el PRIMER candidato individualmente válido que aparece en el
    titular (orden de lectura), extendido localmente hacia adelante mientras
    los tokens contiguos también califiquen ("Redwood" + "Materials",
    "Tailwind" + "CSS"). NO compara la longitud de este candidato contra
    otros candidatos que pudieran existir más adelante en el titular:
    comparar secuencias de posiciones distintas causó regresiones reales
    (auditoría 2026-09-15) — "Nubank acelera su entrada a EE.UU. mediante una
    alianza con Lead Bank" devolvía "Lead Bank" (2 tokens) en vez de "Nubank"
    (1 token, pero es la empresa real del titular y el primer candidato
    válido). La combinación correcta para casos como "Reciclaje... Redwood
    Materials" es que "Reciclaje" quede rechazado en su propia posición por
    ser un sustantivo común (regla 5), no que se compare su longitud contra
    "Redwood Materials".
    """
    if not titulo:
        return None
    # Orden importa: la etiqueta de sección va al INICIO ("Primicia | ...") y
    # el medio al FINAL ("... - El Economista"). Si `_sin_medio` corriera
    # primero sobre un titular con "|", su regex de sufijo (que también
    # reconoce "|" como separador) confundiría TODO lo que sigue al "|" con
    # el "medio" y se comería el titular real completo, dejando solo la
    # etiqueta de sección ("Primicia"). Quitar primero la etiqueta de
    # sección evita esa colisión entre los dos separadores.
    texto = _sin_medio(_sin_prefijo_seccion(titulo))
    tokens = list(re.finditer(r"[\wÁÉÍÓÚÑÜáéíóúñü]+", texto))
    fin_anterior: Optional[int] = None
    saltar_apellido = False
    for idx, m in enumerate(tokens):
        limpio = m.group(0).strip()
        contiguo = fin_anterior is not None and texto[fin_anterior:m.start()].strip() == ""
        es_apellido_descartado = saltar_apellido and contiguo
        saltar_apellido = False
        fin_anterior = m.end()

        if len(limpio) < 3:
            # Siglas cortas de 2 (p. ej. "BQ") son raras; exigimos 3+ salvo sigla.
            if not _es_sigla(limpio):
                continue
        base = _sin_acentos(limpio).lower()
        if base in _STOP_CAP or base in _GENERICOS_SECTOR or base in _SIGLAS_NO_EMPRESA:
            continue
        primera = limpio[0]
        if not (primera.isupper() or _es_sigla(limpio)):
            continue
        if es_apellido_descartado:
            # Apellido contiguo a un nombre de pila ya descartado: parte del
            # mismo nombre de persona, no una organización nueva.
            continue
        if base in _NOMBRES_PROPIOS_PERSONA:
            saltar_apellido = True
            continue
        apellidos_ambiguos = _APELLIDOS_POLITICOS_AMBIGUOS.get(base)
        if apellidos_ambiguos:
            siguiente = tokens[idx + 1] if idx + 1 < len(tokens) else None
            sig_contiguo = (
                siguiente is not None
                and texto[m.end():siguiente.start()].strip() == ""
            )
            if sig_contiguo:
                sig_base = _sin_acentos(siguiente.group(0)).lower()
                if sig_base in apellidos_ambiguos:
                    saltar_apellido = True
                    continue
        if _parece_verbo_conjugado(base):
            continue
        if _parece_sustantivo_comun(base):
            continue

        # Primer candidato individualmente válido: extender hacia adelante
        # mientras los tokens siguientes sean contiguos y cada uno, por sí
        # mismo, también calificaría como candidato, y devolver de inmediato
        # (sin seguir buscando ni comparar contra candidatos posteriores).
        fin_run = m.end()
        j = idx + 1
        while j < len(tokens):
            sig = tokens[j]
            if texto[fin_run:sig.start()].strip() != "":
                break
            if not _token_extiende_candidato(sig.group(0)):
                break
            fin_run = sig.end()
            j += 1
        return texto[m.start():fin_run].strip()

    return None


# ── Marcadores de opinión / tendencia / listículo (léxicos, objetivos) ───────
#
# Presencia de estos patrones en el TITULAR marca contenido de opinión o
# tendencia genérica (no un evento verificable de una empresa). Son cadenas
# fijas comprobables, no criterios ambiguos.
MARCADORES_OPINION: tuple[str, ...] = (
    "opinion", "columna", "editorial", "punto de vista", "analisis",
    "reflexion", "ensayo", "tribuna", "mi opinion", "carta abierta",
    "por que", "porque deberias", "como lograr", "como hacer", "como elegir",
    "guia para", "guia definitiva", "tutorial", "paso a paso",
    "el futuro de", "el fin de", "la era de", "tendencias", "predicciones",
    "lo que viene", "lo que aprendi", "claves para", "consejos para",
    "razones para", "razones por las que", "formas de", "maneras de",
    "ranking de", "los mejores", "las mejores", "top ",
)

# Listículos "5 claves", "10 razones", "3 formas": número + palabra de lista.
_RE_LISTICULO = re.compile(
    r"\b\d{1,3}\s+(claves|razones|formas|maneras|consejos|tips|pasos|"
    r"tendencias|predicciones|errores|habitos|secretos|mitos|preguntas)\b"
)


def es_opinion(titulo: str) -> bool:
    """True si el titular presenta marcadores objetivos de opinión/tendencia."""
    t = _norm(titulo)
    if any(m in t for m in MARCADORES_OPINION):
        return True
    return bool(_RE_LISTICULO.search(t))


# ── Geografía y "no es empresa" (deterministas) ──────────────────────────────
#
# Términos NO-LATAM (país, región, ciudad, gentilicio). El laboratorio opera
# México/LATAM; una nota de España/EE.UU./etc. se descarta.
NO_LATAM: tuple[str, ...] = (
    "espana", "espanola", "espanol", "madrid", "barcelona", "girona", "castilla",
    "cataluna", "andalucia", "sevilla", "galicia", "gallego", "vasco", "catalan",
    "estados unidos", "ee.uu", "eeuu", "reino unido", "inglaterra", "francia",
    "frances", "alemania", "aleman", "italia", "portugal", "china", "india",
    "japon", "canada",
    # Europa y otras regiones fuera de LATAM (se colaban por eventos regulatorios).
    "suiza", "suizo", "europa", "europea", "europeo", "union europea", "bruselas",
    "suecia", "noruega", "dinamarca", "finlandia", "holanda", "paises bajos",
    "belgica", "irlanda", "austria", "grecia", "polonia", "rusia", "ucrania",
    "australia", "corea", "singapur", "hong kong", "dubai", "emiratos", "israel",
)

# Marcas GIGANTES (tecnología global, comida rápida, consumo masivo). No son
# prospectos de HD (empresas en fase de escala con deuda cultural); su aparición
# en un titular casi siempre es ruido internacional, no un candidato LATAM.
#
# Ampliación 2026-09-10 (autorizado por el operador, incidente real: Anthropic
# apareció con ICP 81 por no tener fila en `prospectos` — ver
# app.py:_construir_expedientes, que reutiliza esta MISMA tupla para forzar
# categoria='Corporativo' sin depender de una fila manual). Se agregan
# laboratorios de IA y grandes tecnológicas de capitalización masiva:
# reconocibles por cualquier persona como "gigante tecnológico", nunca startup.
GIGANTES: tuple[str, ...] = (
    "google", "alphabet", "amazon", "aws", "meta", "facebook", "instagram", "whatsapp",
    "apple", "microsoft", "netflix", "tesla", "samsung", "huawei", "tiktok",
    "nvidia", "intel", "spotify", "sony", "disney", "nike", "adidas",
    "wendy", "mcdonald", "burger king", "starbucks", "walmart", "coca-cola",
    "coca cola", "pepsi", "nestle", "unilever",
    # Laboratorios de IA (incidente Anthropic, 2026-09-10).
    "anthropic", "openai", "chatgpt", "deepmind", "mistral ai", "xai",
    "perplexity ai",
    # Grandes tecnológicas de capitalización masiva (mismo criterio, a
    # petición del operador: "cualquier persona reconocería como gigante
    # tecnológico, no como startup").
    "ibm", "oracle", "salesforce", "sap", "cisco", "adobe", "dell",
    "hewlett packard", "hewlett-packard", "qualcomm", "broadcom",
    "servicenow", "palantir", "accenture", "workday",
    # Organizaciones/fundaciones globales reales pero fuera del ICP de HD
    # (no son startups LATAM en escalamiento). Incidente real 2026-09-10.
    "wikimedia",
)

# Términos que indican que NO es una empresa prospecto: gobierno, premios,
# academia, gremios, y REPORTES/análisis de mercado (no una compañía concreta).
NO_EMPRESA: tuple[str, ...] = (
    "gobierno", "ministerio", "ministro", "ayuntamiento", "diputacion",
    "generalitat", "xunta", "alcaldia", "senado", "congreso",
    "premios", "premio", "galardon",
    "universidad", "facultad", "camara de", "colegio de",
    "asociacion", "federacion", "fundacion", "sindicato",
    "panorama de", "panorama del", "outlook", "perspectivas de",
    "perspectivas para", "estado de la", "el estado de", "balance de",
    "resumen del ano", "reporte anual", "informe anual", "state of",
    "de cada 10", "de cada diez", "siete de cada", "record en", "ranking",
    "radiografia",
    # Sucesos / nota roja / interés humano: no son una empresa prospecto.
    "muerte de", "muere ", "murio", "fallece", "fallecio", "asesinat",
    "asesinan", "homicidio", "feminicidio", "femicidio", "violencia de genero",
    "violencia de genero", "accidente", "detienen a", "detenido", "detenida",
    "narco", "secuestro", "balacera", "sismo", "terremoto", "huracan",
    "elecciones", "candidato", "candidata", "partido politico",
)

# Ruido mediático que NO es inteligencia de organización: deportes, espectáculos,
# clima, promociones y aperturas rutinarias. Estas notas nunca son un prospecto
# ni una señal estratégica; se descartan de la evidencia antes de mostrarse.
RUIDO_MEDIATICO: tuple[str, ...] = (
    # Deportes
    "futbol", "liga mx", "mundial", "champions", "nba", "nfl", "beisbol",
    "boxeo", "seleccion nacional", "gol de", "goles de", "partido de",
    # Espectáculos / entretenimiento / farándula
    "farandula", "espectaculos", "celebridad", "telenovela", "reality show",
    "alfombra roja", "concierto de", "estreno de la pelicula", "cantante",
    # Clima / desastres naturales
    "ola de calor", "frente frio", "granizada", "deslave", "inundacion",
    "tormenta tropical", "lluvias",
    # Promociones / ofertas / patrocinado
    "promocion", "descuento", "cupon", "oferta especial", "2x1", "rebajas",
    "contenido patrocinado", "nota patrocinada", "publirreportaje",
    # Aperturas rutinarias / obituarios
    "abre sucursal", "abre su sucursal", "nueva sucursal", "inaugura",
    "inauguracion", "franquicia", "obituario", "esquela",
)

# Eventos que involucran a una empresa pero NO tienen profundidad estructural
# para Thick Data. Pasan los filtros existentes (no opinión, no gigante, tienen
# empresa) pero NO son evidencia de fricción cultural. El laboratorio descarta
# esto ANTES de persistir: el sistema es un curador, no un recolector.
EVENTOS_SUPERFICIALES: tuple[str, ...] = (
    # Imagen corporativa / PR / marca — sin fricción
    "patrocinio", "patrocina", "sponsor", "naming rights",
    "responsabilidad social", "accion social", "voluntariado",
    "donacion a", "dona a", "dona millones",
    "aniversario de", "cumple anos", "celebra su aniversario",
    # Operaciones rutinarias — sin señal estructural
    "nueva version de", "actualizacion de", "actualiza su app",
    "cambio de imagen", "cambio de logo", "rebranding",
    # Eventos de industria sin impacto estructural
    "participa en", "participara en", "asiste a", "asistira a",
    "presenta en", "presento en", "conferencia de", "foro de",
    "summit", "webinar", "hackathon", "meetup",
    # Reconocimientos — positivos pero sin Thick Data
    "mejor empresa para trabajar", "great place to work",
    "reconocida como", "obtiene certificacion", "certificada como",
    # Comentario de mercado sin evento estructural
    "analistas esperan", "los expertos opinan", "valoracion de mercado",
    "cotiza a", "sube en bolsa", "baja en bolsa", "accion de",
    "acciones de", "precio objetivo",
)

# Título de reporte: un tema seguido de "AÑO:" (p. ej. "Venture Capital LATAM
# 2025:"). Señal fuerte de informe, casi nunca una empresa.
_RE_REPORTE = re.compile(r"\b20\d\d\s*:")


def _contiene(texto: str, terminos: tuple[str, ...]) -> bool:
    return any(t in texto for t in terminos)


# ── Filtro de relevancia mínimo ──────────────────────────────────────────────
#
# Motivos de descarte (se persisten en `rechazos`, auditables):
MOTIVO_OPINION = "relevancia:opinion"          # opinión / tendencia / listículo
MOTIVO_SIN_EMPRESA = "relevancia:sin_empresa"  # no menciona empresa concreta
MOTIVO_SIN_EVENTO = "relevancia:sin_evento"    # no describe evento verificable
MOTIVO_NO_LATAM = "relevancia:no_latam"        # geografía fuera de LATAM
MOTIVO_NO_EMPRESA = "relevancia:no_empresa"    # gobierno/premios/academia/reporte/suceso
MOTIVO_GIGANTE = "relevancia:gigante"          # marca gigante (no es ICP de HD)
MOTIVO_RUIDO = "relevancia:ruido_mediatico"    # deportes/espectáculos/clima/promos/aperturas
MOTIVO_SUPERFICIAL = "relevancia:sin_profundidad_estructural"  # evento sin Thick Data


def evaluar_relevancia(
    titulo: str, keywords: list, empresa_identificada: bool,
    exigir_evento: bool = True, organizacion: str = "",
) -> tuple[bool, str]:
    """Decide si un titular de descubrimiento es relevante. Determinista.

    Filosofía: el sistema es un curador de Thick Data, no un recolector de
    noticias. Filtra agresivamente buscando indicios de fricción estructural,
    Deuda Cultural, Situacional o Simbólica.

    Reglas (todas deben cumplirse para CONSERVAR):
      R1  No es opinión/tendencia/listículo (marcadores léxicos).
      R2  No es geografía fuera de LATAM (España, EE.UU., …).
      R3  No es "no-empresa" (gobierno, premios, academia, reporte de mercado).
      R4  No es ruido mediático (deportes, espectáculos, clima, promos).
      R5  La organización IDENTIFICADA no es una marca gigante global (no es
          perfil HD). IDENTIDAD ≠ RELACIÓN/CONTEXTO (corrección 2026-09-11,
          autorizada por el operador): que el titular MENCIONE un gigante por
          alianza, competencia, financiamiento, ecosistema o adquisición junto
          a una startup real ya identificada no descarta la evidencia — el
          Motor A identifica y cura organizaciones, no confunde la presencia
          de un corporativo en el contexto con la identidad corporativa del
          prospecto. Si ``organizacion`` no se provee (compatibilidad), se
          conserva el criterio anterior sobre el titular completo.
      R6  No es evento superficial sin profundidad estructural (PR, premios,
          conferencias, movimientos bursátiles rutinarios).
      R7  Hay una empresa identificable (nombre propio o consulta dirigida).
      R8  (solo si ``exigir_evento``) Hay un evento verificable en ``keywords``.

    Devuelve ``(relevante, motivo)``. ``motivo`` vacío si es relevante.
    """
    t = _norm(titulo)
    if es_opinion(titulo):
        return False, MOTIVO_OPINION
    if _contiene(t, NO_LATAM):
        return False, MOTIVO_NO_LATAM
    if _contiene(t, NO_EMPRESA) or _RE_REPORTE.search(t):
        return False, MOTIVO_NO_EMPRESA
    if _contiene(t, RUIDO_MEDIATICO):
        return False, MOTIVO_RUIDO
    objetivo_gigante = _norm(organizacion) if organizacion else t
    if _contiene(objetivo_gigante, GIGANTES):
        return False, MOTIVO_GIGANTE
    if _contiene(t, EVENTOS_SUPERFICIALES):
        return False, MOTIVO_SUPERFICIAL
    if not empresa_identificada:
        return False, MOTIVO_SIN_EMPRESA
    if exigir_evento and not keywords:
        return False, MOTIVO_SIN_EVENTO
    return True, ""


# ── Calidad de captura (informativa) ─────────────────────────────────────────
#
# Etiqueta objetiva del acto de captura. NO es una puntuación de valor comercial
# (eso es del Motor B). Se calcula con cuatro criterios objetivos:
#   c1  empresa claramente identificada,
#   c2  evento claramente identificado (señal genérica presente),
#   c3  fuente confiable (medio nombrado, no fuente genérica),
#   c4  ausencia de duplicados (garantizada: solo se etiquetan registros que
#       pasaron la deduplicación robusta).
CALIDAD_ALTA = "Alta"
CALIDAD_MEDIA = "Media"
CALIDAD_BAJA = "Baja"


def calcular_calidad(
    empresa_ok: bool, evento_ok: bool, fuente_ok: bool, sin_duplicado: bool = True
) -> str:
    """Etiqueta de calidad de captura (Alta|Media|Baja) por criterios objetivos.

    ``sin_duplicado`` es True para todo registro almacenado (la dedup ya corrió),
    por lo que actúa como criterio siempre satisfecho; la etiqueta la determinan
    los tres criterios variables (empresa, evento, fuente):
        3 de 3  -> Alta      2 de 3 -> Media      <=1 de 3 -> Baja
    """
    n = int(bool(empresa_ok)) + int(bool(evento_ok)) + int(bool(fuente_ok))
    if not sin_duplicado:
        return CALIDAD_BAJA
    if n >= 3:
        return CALIDAD_ALTA
    if n == 2:
        return CALIDAD_MEDIA
    return CALIDAD_BAJA
