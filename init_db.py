import sqlite3, os

db_path = os.path.expanduser("~/antrosapiens/antrolab.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.executescript("""
-- 1. SEÑAL Y CAPA 0 (Hecho, Scraping Antropológico, Materialidad)
CREATE TABLE IF NOT EXISTS senal_raw (
    evidence_id TEXT PRIMARY KEY,
    url TEXT,
    dominio TEXT,
    captured_at TEXT,
    titulo TEXT,
    cuerpo_disponible TEXT,
    organizacion_mencionada TEXT,
    fuente_medio TEXT,
    fragmento_textual TEXT,
    hash_contenido TEXT UNIQUE,
    metodo_captura TEXT DEFAULT 'scraping_antropologico'
);

-- 2. POSICIÓN DEL ENUNCIADOR (Principio 5, 18, 20)
CREATE TABLE IF NOT EXISTS enunciador_posicion (
    evidence_id TEXT PRIMARY KEY,
    quien_habla TEXT,               -- Actor / Categoria
    desde_donde TEXT,              -- Posicion social / Jerarquia
    para_quien TEXT,               -- Audiencia / Canal
    relacion_poder TEXT,           -- Asimetria / Interes / Exposicion
    FOREIGN KEY(evidence_id) REFERENCES senal_raw(evidence_id)
);

-- 3. SITUACIÓN Y TENSIÓN (Principios 1, 3, 10, 11, 12, 14)
CREATE TABLE IF NOT EXISTS tension_situacional (
    tension_id TEXT PRIMARY KEY,
    evidence_id TEXT,
    organizacion TEXT,
    relacion_observada TEXT,       -- Unidad de analisis (Principio 2)
    discurso_declarado TEXT,      -- Lo que dicen (Principio 3)
    practica_efectiva TEXT,        -- Lo que hacen (Principio 3)
    friccion_detectada TEXT,       -- Friccion (Principio 11)
    deuda_cultural TEXT,           -- Atajos/Rituales/Soluciones invisibles (Principios 12, 13, 14)
    FOREIGN KEY(evidence_id) REFERENCES senal_raw(evidence_id)
);

-- 4. PATRÓN E HIPÓTESIS ANTROPOLÓGICA (Principios 8, 24, 25, 39)
CREATE TABLE IF NOT EXISTS hipotesis_antropologica (
    hipotesis_id TEXT PRIMARY KEY,
    organizacion TEXT,
    recurrencia_patron TEXT,       -- Recurrencia / Corpus (Principios 8, 24)
    hipotesis_texto TEXT,          -- Hipotesis trazable (Principio 39)
    epistemologia_privilegiada TEXT DEFAULT 'Decolonial / Situada', -- (Principio 28)
    nivel_confianza TEXT CHECK(nivel_confianza IN ('BAJO', 'MEDIO', 'ALTO'))
);

-- Relacion N:M entre Evidencias e Hipotesis (Triangulacion - Principio 25)
CREATE TABLE IF NOT EXISTS triangulacion_evidencia (
    hipotesis_id TEXT,
    evidence_id TEXT,
    PRIMARY KEY(hipotesis_id, evidence_id),
    FOREIGN KEY(hipotesis_id) REFERENCES hipotesis_antropologica(hipotesis_id),
    FOREIGN KEY(evidence_id) REFERENCES senal_raw(evidence_id)
);

-- 5. DECISIÓN Y HUMAN BLOCK (Principios 6, 27, 40, No Simulación)
CREATE TABLE IF NOT EXISTS decision_laboratorio (
    organizacion TEXT PRIMARY KEY,
    estado TEXT CHECK(estado IN ('CASO_CANDIDATO', 'OBSERVAR', 'RECHAZADO')),
    dictamen_humano TEXT,
    reflexividad_investigador TEXT, -- (Principio 27)
    decidido_en TEXT
);
""")

conn.commit()
conn.close()
print("-> Base de datos reestructurada según el Lienzo de Principios Antropológicos.")
