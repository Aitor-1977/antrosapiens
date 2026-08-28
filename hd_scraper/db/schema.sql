-- Esquema de hd-scraper.
-- Escrito en SQL portable: usa tipos e idioms que existen tanto en SQLite
-- como en PostgreSQL. Notas de migración a Postgres:
--   * INTEGER PRIMARY KEY AUTOINCREMENT  -> GENERATED ALWAYS AS IDENTITY / BIGSERIAL
--   * las fechas se guardan como TEXT ISO 8601 (portable; en Postgres se puede
--     migrar la columna a TIMESTAMPTZ sin tocar el modelo).
--   * INSERT ... ON CONFLICT existe en ambos motores.

-- Evidencias: registros que CUMPLEN el contrato. Nunca entra aquí un registro
-- incompleto (eso va a `rechazos`). `estado` distingue consumibles de no_fechado.
CREATE TABLE IF NOT EXISTS evidencias (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Contrato obligatorio
    cita_textual        TEXT NOT NULL,
    fecha_extraccion    TEXT NOT NULL,          -- ISO 8601
    url_fuente          TEXT NOT NULL,
    nombre_medio        TEXT NOT NULL,
    empresa_mencionada  TEXT NOT NULL,
    tipo_evento         TEXT NOT NULL,          -- literal: ronda|contratacion|despido|lanzamiento|queja|cambio_sitio
    origen_declaracion  TEXT NOT NULL,          -- literal: operador|inversor|prensa|usuario
    hash_dedup          TEXT NOT NULL UNIQUE,   -- sha256(empresa + url normalizada)
    -- Contrato opcional
    fecha_publicacion   TEXT,                   -- ISO 8601; NULL => estado no_fechado
    persona_citada      TEXT,
    cargo               TEXT,
    -- Metadatos internos
    connector           TEXT NOT NULL,
    estado              TEXT NOT NULL DEFAULT 'ok',  -- ok | no_fechado
    raw_hash            TEXT,                   -- enlace al crudo retenido (raw_store)
    categoria           TEXT,                   -- ecosistema si viene de descubrimiento por categoría
    keywords            TEXT,                   -- JSON: etiquetas de señal Nivel 1 (objetivas)
    confianza           REAL NOT NULL DEFAULT 0, -- calidad objetiva de la extracción 0–1
    -- Captura Inteligente (dedup robusto + calidad informativa)
    clave_contenido     TEXT,                   -- identidad de contenido (url:/txt:) para dedup robusto
    hash_contenido      TEXT,                   -- sha256 del título normalizado (dedup entre URLs distintas)
    calidad_captura     TEXT,                   -- Alta | Media | Baja (informativa; no altera el scoring)
    creado_en           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidencias_empresa ON evidencias (empresa_mencionada);
CREATE INDEX IF NOT EXISTS idx_evidencias_tipo    ON evidencias (tipo_evento);
CREATE INDEX IF NOT EXISTS idx_evidencias_estado  ON evidencias (estado);
CREATE INDEX IF NOT EXISTS idx_evidencias_fpub    ON evidencias (fecha_publicacion);
CREATE INDEX IF NOT EXISTS idx_evidencias_categoria ON evidencias (categoria);
CREATE INDEX IF NOT EXISTS idx_evidencias_clave  ON evidencias (clave_contenido);
CREATE INDEX IF NOT EXISTS idx_evidencias_hashc  ON evidencias (hash_contenido);

-- Rechazos: todo registro que no pasa el validador, con su motivo. Auditable.
CREATE TABLE IF NOT EXISTS rechazos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    connector     TEXT NOT NULL,
    motivo        TEXT NOT NULL,
    payload_json  TEXT NOT NULL,   -- registro crudo/normalizado que se rechazó
    creado_en     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rechazos_motivo ON rechazos (motivo);

-- Prospectos: entidades objetivo de los CUATRO ecosistemas estratégicos.
-- `categoria` es OBLIGATORIA y acotada por CHECK (portable a SQLite y Postgres).
-- Los campos de "Thick Data" guardan el discurso corporativo extraído de URLs o
-- perfiles: el motor los ALMACENA tal cual, no los interpreta.
CREATE TABLE IF NOT EXISTS prospectos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                TEXT NOT NULL,
    categoria             TEXT NOT NULL,   -- VC | Startup | Incubadora | Corporativo
    -- Perfil de la entidad
    vertical              TEXT,            -- sector/vertical (declarado o del sitio)
    sitio_web             TEXT,            -- URL del sitio oficial
    linkedin              TEXT,            -- enlace a LinkedIn
    -- Thick Data (discurso corporativo)
    discurso_corporativo  TEXT,            -- cuerpo de texto extraído (tesis, promesa, programa, comunicado…)
    tipo_discurso         TEXT,            -- etiqueta estructural (tesis_inversion|promesa_valor|programa|portafolio|comunicado|reporte|perfil)
    url_perfil            TEXT,            -- URL/perfil de donde se extrajo el discurso
    fuente_discurso       TEXT,            -- nombre de la fuente/plataforma
    fecha_captura         TEXT,            -- ISO 8601 de la captura del texto
    -- Escala/tamaño: parámetro estructural OBLIGATORIO extraído de la fuente
    -- orgánica. 'indeterminada' cuando la fuente no lo declara (patrón no_fechado).
    escala                TEXT NOT NULL DEFAULT 'indeterminada',
    -- Metadatos
    hash_dedup            TEXT NOT NULL UNIQUE,  -- sha256(nombre normalizado + categoria)
    creado_en             TEXT NOT NULL,
    actualizado_en        TEXT NOT NULL,
    CHECK (categoria IN ('VC', 'Startup', 'Incubadora', 'Corporativo'))
);

CREATE INDEX IF NOT EXISTS idx_prospectos_categoria ON prospectos (categoria);
CREATE INDEX IF NOT EXISTS idx_prospectos_nombre    ON prospectos (nombre);

-- Cola de trabajos: reemplaza a Redis con una tabla simple en SQLite.
CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    connector     TEXT NOT NULL,
    query_json    TEXT NOT NULL,   -- QuerySpec serializado
    estado        TEXT NOT NULL DEFAULT 'pending',  -- pending|running|done|error
    intentos      INTEGER NOT NULL DEFAULT 0,
    resultado     TEXT,
    creado_en     TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_estado ON jobs (estado);

-- Salud por fuente: una fila por conector.
CREATE TABLE IF NOT EXISTS salud_fuentes (
    fuente               TEXT PRIMARY KEY,
    ultima_corrida       TEXT,
    ultimo_estado        TEXT,    -- ok | error
    fallos_consecutivos  INTEGER NOT NULL DEFAULT 0,
    alerta               INTEGER NOT NULL DEFAULT 0,  -- 0/1 (boolean portable)
    detalle              TEXT
);

-- Retención del crudo comprimido en disco, vinculado por hash_dedup.
CREATE TABLE IF NOT EXISTS raw_store (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_dedup  TEXT NOT NULL,
    path        TEXT NOT NULL,   -- ruta del .gz en disco
    formato     TEXT NOT NULL,   -- json | xml | html
    tamano      INTEGER NOT NULL,
    creado_en   TEXT NOT NULL,   -- ISO 8601
    expira_en   TEXT NOT NULL    -- ISO 8601 (creado_en + retención)
);

CREATE INDEX IF NOT EXISTS idx_raw_hash   ON raw_store (hash_dedup);
CREATE INDEX IF NOT EXISTS idx_raw_expira ON raw_store (expira_en);

-- Caché de respuestas del directorio de empresas (Wikidata). Evita repetir la
-- misma consulta a la base pública; se sirve desde aquí si tiene < 7 días.
CREATE TABLE IF NOT EXISTS directorio_cache (
    clave       TEXT PRIMARY KEY,   -- qids|limite (la respuesta no depende de la vertical)
    data_json   TEXT NOT NULL,      -- respuesta cruda de Wikidata (JSON)
    creado_en   TEXT NOT NULL       -- ISO 8601
);

-- Señales de la Capa 0: matches deterministas del motor de reglas sobre texto
-- (titulares, descripciones o transcripciones de video). id determinista => dedup.
CREATE TABLE IF NOT EXISTS senales_capa0 (
    id                TEXT PRIMARY KEY,   -- sha1(url|tipo|kw)
    url               TEXT,
    timestamp_video   TEXT,
    fragmento_literal TEXT,
    tipo_senal        TEXT,               -- Operativa | Discursiva | Rescate
    score_deuda       REAL,
    motivo_match      TEXT,
    org_id            TEXT,
    org_nombre        TEXT,
    score_total       REAL,
    nivel_alerta      TEXT,               -- Normal | Crítica
    creado_en         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_capa0_org    ON senales_capa0 (org_nombre);
CREATE INDEX IF NOT EXISTS idx_capa0_alerta ON senales_capa0 (nivel_alerta);

-- Investigaciones (informes) guardadas: snapshot con su Markdown y resumen.
CREATE TABLE IF NOT EXISTS informes_guardados (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo        TEXT,
    categorias    TEXT,          -- ecosistemas incluidos (coma-separados)
    total         INTEGER,
    resumen_json  TEXT,          -- {A,B,C}
    markdown      TEXT,
    creado_en     TEXT NOT NULL
);

-- =========================================================================
-- Capa 6 — Motor de Drift Narrativo
-- Snapshots versionados del discurso público de cada organización.
-- Cada snapshot captura el texto limpio de una página pública en un momento
-- dado. La comparación entre snapshots consecutivos genera evidencias
-- narrativas (cambios observados, no interpretados).
-- =========================================================================

CREATE TABLE IF NOT EXISTS drift_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre          TEXT NOT NULL,
    tipo_pagina         TEXT NOT NULL,       -- homepage|about|mision|propuesta_valor|manifiesto
    url                 TEXT NOT NULL,
    texto               TEXT NOT NULL DEFAULT '',
    hash_contenido      TEXT NOT NULL DEFAULT '',
    estado_observable   TEXT NOT NULL DEFAULT 'ok',  -- ok|no_observable|spa|error_http|timeout|contenido_vacio|bloqueado|robots
    capturado_en        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_drift_snap_org   ON drift_snapshots (org_nombre);
CREATE INDEX IF NOT EXISTS idx_drift_snap_tipo  ON drift_snapshots (tipo_pagina);
CREATE INDEX IF NOT EXISTS idx_drift_snap_hash  ON drift_snapshots (hash_contenido);

-- Evidencias Narrativas: cambios detectados entre snapshots consecutivos.
-- Cada evidencia es un HECHO observado (no una interpretación). Los tipos
-- están cerrados: posicionamiento|audiencia|lenguaje|identidad|concepto_nuevo|
-- concepto_eliminado|contradiccion|cambio_ontologico.
CREATE TABLE IF NOT EXISTS drift_evidencias (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre            TEXT NOT NULL,
    tipo_cambio           TEXT NOT NULL,
    tipo_pagina           TEXT NOT NULL,
    fragmento_antes       TEXT,
    fragmento_despues     TEXT,
    descripcion           TEXT NOT NULL,
    snapshot_anterior_id  INTEGER REFERENCES drift_snapshots(id),
    snapshot_actual_id    INTEGER REFERENCES drift_snapshots(id),
    hash_dedup            TEXT NOT NULL UNIQUE,
    detectado_en          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_drift_ev_org  ON drift_evidencias (org_nombre);
CREATE INDEX IF NOT EXISTS idx_drift_ev_tipo ON drift_evidencias (tipo_cambio);

-- =========================================================================
-- Capa 7 — Motor Onlife
-- Señales conductuales observadas en espacios digitales donde la vida
-- organizacional realmente ocurre (repos, foros, changelogs, comunidades).
-- Cada señal es un HECHO verificable con URL fuente. No interpreta.
-- =========================================================================

CREATE TABLE IF NOT EXISTS onlife_signals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre          TEXT NOT NULL,
    fuente              TEXT NOT NULL,       -- github|hackernews|blog_changelog
    tipo_senal          TEXT NOT NULL,       -- actividad_tech|lanzamiento|comunidad|contratacion|presencia
    dato_json           TEXT NOT NULL,       -- observación estructurada (JSON)
    url                 TEXT,
    descripcion         TEXT NOT NULL,       -- descripción legible del hecho observado
    fecha_observacion   TEXT NOT NULL,       -- ISO 8601
    hash_dedup          TEXT NOT NULL UNIQUE,
    creado_en           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_onlife_org    ON onlife_signals (org_nombre);
CREATE INDEX IF NOT EXISTS idx_onlife_fuente ON onlife_signals (fuente);
CREATE INDEX IF NOT EXISTS idx_onlife_tipo   ON onlife_signals (tipo_senal);

-- =========================================================================
-- Capa 9 — Pipeline Comercial
-- Gestión de etapas por organización basada en evidencia antropológica.
-- Reemplaza la lógica CRM: el avance depende de evidencia acumulada,
-- no de intención de venta.
-- Etapas: observacion → vigilancia → peritaje → dolormap → alianza → cerrado
-- =========================================================================

CREATE TABLE IF NOT EXISTS pipeline_comercial (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre       TEXT NOT NULL,
    etapa            TEXT NOT NULL DEFAULT 'observacion',
    notas            TEXT NOT NULL DEFAULT '',
    resultado        TEXT NOT NULL DEFAULT '',   -- ganado|descartado|pausado (solo en cerrado)
    hash_dedup       TEXT NOT NULL UNIQUE,       -- sha256(org_nombre normalizado)
    candidato_id     TEXT,                       -- identidad referencial del candidato (BC-I→BC-II)
    creado_en        TEXT NOT NULL,
    actualizado_en   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_etapa ON pipeline_comercial (etapa);
CREATE INDEX IF NOT EXISTS idx_pipeline_org   ON pipeline_comercial (org_nombre);
-- `idx_pipeline_candidato` se crea en `database._migrar_pipeline_candidato`
-- DESPUÉS del ALTER: en bases preexistentes la columna no existe aún cuando
-- `executescript` corre, y el índice sobre una columna ausente rompería la
-- migración de bases legacy.

CREATE TABLE IF NOT EXISTS pipeline_transiciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id     INTEGER NOT NULL REFERENCES pipeline_comercial(id),
    org_nombre      TEXT NOT NULL,
    etapa_desde     TEXT NOT NULL DEFAULT '',
    etapa_hasta     TEXT NOT NULL,
    notas           TEXT NOT NULL DEFAULT '',
    fecha           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trans_pipeline ON pipeline_transiciones (pipeline_id);
CREATE INDEX IF NOT EXISTS idx_trans_fecha    ON pipeline_transiciones (fecha);

-- =========================================================================
-- Reparación BC-I ↔ BC-II — Candidatos Comerciales (identidad referencial)
-- Cada organización detectada por Motor A (BC-I) se materializa como un
-- Candidato Comercial independiente y trazable (BC-II). Sustituye la unión
-- NOMINAL por nombre/hash_dedup por una identidad referencial determinista:
--   organización → candidato → prospecto → expediente → evidencia.
-- `candidato_id` = sha256(normalizar_empresa(org_nombre)): estable y
-- determinista (reprocesar la misma organización produce el mismo ID).
-- `hash_dedup` = hash legacy de pipeline_comercial, para compat 1:1 con los
-- datos existentes (los registros de pipeline de hoy no se rompen).
-- =========================================================================

CREATE TABLE IF NOT EXISTS candidatos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    candidato_id     TEXT NOT NULL UNIQUE,       -- ID estable por organización/candidato
    org_nombre       TEXT NOT NULL,              -- nombre de la organización observada (BC-I)
    organizacion_id  INTEGER,                    -- snapshot del índice estable de observatorio._id_map
    estado           TEXT NOT NULL DEFAULT 'detectado',  -- detectado|observado|descartado
    prospecto_id     INTEGER REFERENCES prospectos(id),  -- enlace referencial al prospecto (BC-II)
    expediente_hash  TEXT,                       -- hash de la huella del expediente (BC-I)
    hash_dedup       TEXT NOT NULL UNIQUE,       -- compat legacy con pipeline_comercial
    creado_en        TEXT NOT NULL,
    actualizado_en   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidatos_estado ON candidatos (estado);
CREATE INDEX IF NOT EXISTS idx_candidatos_org    ON candidatos (org_nombre);

-- Cada transición (Detectado/Observado/Descartado) conserva la referencia a la
-- evidencia que la sustenta: `evidencia_id` (evidencias.id) + url/texto
-- (referencias estables denormalizadas) + `expediente_hash` vigente.
CREATE TABLE IF NOT EXISTS candidato_transiciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    candidato_id    TEXT NOT NULL REFERENCES candidatos(candidato_id),
    org_nombre      TEXT NOT NULL,
    estado_desde    TEXT NOT NULL DEFAULT '',
    estado_hasta    TEXT NOT NULL,
    notas           TEXT NOT NULL DEFAULT '',
    evidencia_id    INTEGER REFERENCES evidencias(id),
    evidencia_url   TEXT,
    evidencia_texto TEXT,
    expediente_hash TEXT,
    fecha           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidato_trans_cand ON candidato_transiciones (candidato_id);
CREATE INDEX IF NOT EXISTS idx_candidato_trans_fecha ON candidato_transiciones (fecha);

-- =========================================================================
-- Capa 12 — Gobernanza Científica, Auditoría Total y Reproducibilidad
-- Persiste huellas digitales, versionado, bitácora de decisiones, auditorías
-- y certificados. NO reinterpreta: solo almacena lo que la capa pura calculó.
-- Escritura idempotente por hash/id (select-then-insert), 100% determinista.
-- =========================================================================

CREATE TABLE IF NOT EXISTS versionado_modelo (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    componente     TEXT NOT NULL,
    version        TEXT NOT NULL,
    hash_contenido TEXT NOT NULL,
    registrado_en  TEXT NOT NULL,
    UNIQUE (componente, hash_contenido)
);

CREATE INDEX IF NOT EXISTS idx_versionado_comp ON versionado_modelo (componente);

CREATE TABLE IF NOT EXISTS huellas_digitales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre     TEXT NOT NULL,
    huella_id      TEXT NOT NULL,
    hash           TEXT NOT NULL UNIQUE,
    version        TEXT NOT NULL,
    versiones_json TEXT NOT NULL DEFAULT '{}',
    hashes_json    TEXT NOT NULL DEFAULT '{}',
    fecha          TEXT NOT NULL,
    creado_en      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_huellas_org  ON huellas_digitales (org_nombre);
CREATE INDEX IF NOT EXISTS idx_huellas_hash ON huellas_digitales (hash);

CREATE TABLE IF NOT EXISTS bitacora_decisiones (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre        TEXT NOT NULL,
    hash_expediente   TEXT NOT NULL,
    tipo              TEXT NOT NULL,
    regla             TEXT NOT NULL,
    resultado         TEXT NOT NULL,
    detalle           TEXT NOT NULL DEFAULT '',
    version_algoritmo TEXT NOT NULL,
    registrado_en     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bitacora_org  ON bitacora_decisiones (org_nombre);
CREATE INDEX IF NOT EXISTS idx_bitacora_hash ON bitacora_decisiones (hash_expediente);
CREATE INDEX IF NOT EXISTS idx_bitacora_tipo ON bitacora_decisiones (tipo);

CREATE TABLE IF NOT EXISTS auditoria_expedientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre      TEXT NOT NULL,
    hash_expediente TEXT NOT NULL UNIQUE,
    veredicto       TEXT NOT NULL DEFAULT '',
    integra         INTEGER NOT NULL DEFAULT 0,
    consistente     INTEGER NOT NULL DEFAULT 0,
    reproducible    INTEGER NOT NULL DEFAULT 0,
    auditoria_json  TEXT NOT NULL DEFAULT '{}',
    creado_en       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auditoria_org ON auditoria_expedientes (org_nombre);

CREATE TABLE IF NOT EXISTS certificados (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre        TEXT NOT NULL,
    certificado_id    TEXT NOT NULL UNIQUE,
    hash              TEXT NOT NULL,
    version           TEXT NOT NULL,
    estado            TEXT NOT NULL,
    veredicto         TEXT NOT NULL,
    nivel_evidencia   TEXT NOT NULL DEFAULT '',
    nivel_confianza   TEXT NOT NULL DEFAULT '',
    solidez           INTEGER NOT NULL DEFAULT 0,
    suficiencia       INTEGER NOT NULL DEFAULT 0,
    firma_motor       TEXT NOT NULL,
    fecha             TEXT NOT NULL,
    certificado_json  TEXT NOT NULL DEFAULT '{}',
    creado_en         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_certificados_org  ON certificados (org_nombre);
CREATE INDEX IF NOT EXISTS idx_certificados_hash ON certificados (hash);

-- =========================================================================
-- Capa 13 — Memoria Científica (append-only, inmutable)
-- Conserva TODAS las versiones históricas de cada expediente. Nunca UPDATE ni
-- DELETE. version_num monótono por organización; dedup por hash de huella.
-- =========================================================================

CREATE TABLE IF NOT EXISTS memoria_cientifica (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    org_nombre      TEXT NOT NULL,
    version_num     INTEGER NOT NULL,
    hash            TEXT NOT NULL,
    hash_previo     TEXT NOT NULL DEFAULT '',
    veredicto       TEXT NOT NULL DEFAULT '',
    scoring         TEXT NOT NULL DEFAULT '',
    hipotesis       TEXT NOT NULL DEFAULT '',
    solidez         INTEGER NOT NULL DEFAULT 0,
    suficiencia     INTEGER NOT NULL DEFAULT 0,
    nivel_evidencia TEXT NOT NULL DEFAULT '',
    nivel_confianza TEXT NOT NULL DEFAULT '',
    dolor_cultural  TEXT NOT NULL DEFAULT '',
    snapshot_json   TEXT NOT NULL DEFAULT '{}',
    motor           TEXT NOT NULL DEFAULT '',
    pipeline        TEXT NOT NULL DEFAULT '',
    usuario         TEXT NOT NULL DEFAULT 'sistema',
    creado_en       TEXT NOT NULL,
    UNIQUE (org_nombre, version_num)
);

CREATE INDEX IF NOT EXISTS idx_memoria_org  ON memoria_cientifica (org_nombre);
CREATE INDEX IF NOT EXISTS idx_memoria_hash ON memoria_cientifica (hash);

-- ── Clasificación epistemológica de la evidencia (Entrega 2) ───────────────
-- Espejo SQLite de las tablas ya existentes en producción (Neon). Se declaran
-- aquí para que los tests corran sin Postgres. `IF NOT EXISTS` garantiza que
-- una base que ya las tiene no se toca.
--
-- No llevan índice único sobre `evidencia_id` ni sobre `organizacion`: así
-- están en producción y no se modifican desde el código. La idempotencia de la
-- reejecución vive en `clasificacion_store.py` (LEFT JOIN + SELECT previo).

CREATE TABLE IF NOT EXISTS expedientes_candidatos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    organizacion    TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'abierto',
    creado_en       TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en  TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT chk_estado CHECK (estado IN ('abierto','candidato','descartado'))
);

CREATE TABLE IF NOT EXISTS evidencia_clasificada (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id       INTEGER NOT NULL REFERENCES expedientes_candidatos(id),
    evidencia_id        INTEGER NOT NULL REFERENCES evidencias(id),
    tipo_epistemologico TEXT NOT NULL,
    enunciador_nombre   TEXT,
    enunciador_cargo    TEXT,
    enunciador_dominio  TEXT,
    -- Organización explícitamente mencionada en el texto (extracción
    -- estructural, no la frase de búsqueda de conectores de descubrimiento
    -- amplio). NULL cuando no hay patrón fuerte de aposición/fundación en el
    -- texto — nunca se inventa. Ver CLAUDE.md "Frontera de Interpretación".
    organizacion_mencionada TEXT,
    creado_en           TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT chk_tipo CHECK (tipo_epistemologico IN (
        'senal_primaria_autodeclaracion',
        'senal_primaria_huella_practica',
        'corroborante',
        'contextual'
    ))
);

CREATE INDEX IF NOT EXISTS idx_evclas_evidencia   ON evidencia_clasificada (evidencia_id);
CREATE INDEX IF NOT EXISTS idx_evclas_expediente  ON evidencia_clasificada (expediente_id);
CREATE INDEX IF NOT EXISTS idx_expcand_org        ON expedientes_candidatos (organizacion);
