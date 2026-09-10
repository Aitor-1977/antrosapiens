CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS familias_antropologicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    orden INTEGER
);

CREATE TABLE IF NOT EXISTS principios_antropologicos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    familia VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    pregunta_control TEXT NOT NULL,
    es_nucleo_duro BOOLEAN DEFAULT false,
    activo BOOLEAN DEFAULT true,
    version VARCHAR(20) DEFAULT '1.0'
);

CREATE TABLE IF NOT EXISTS fuentes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT,
    dominio VARCHAR(255),
    tipo_fuente VARCHAR(100),
    titulo TEXT,
    fecha_publicacion TIMESTAMP WITH TIME ZONE,
    fecha_captura TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    autor VARCHAR(255),
    estado_fuente VARCHAR(50) DEFAULT 'ACTIVA',
    hash_contenido VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS organizaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(100),
    sector VARCHAR(100),
    territorio VARCHAR(100),
    descripcion TEXT,
    situacion_actual TEXT,
    nivel_relevancia INTEGER DEFAULT 1,
    estado_investigacion VARCHAR(50) DEFAULT 'EN_OBSERVACION'
);

CREATE TABLE IF NOT EXISTS actores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    tipo_actor VARCHAR(50) NOT NULL,
    cargo VARCHAR(255),
    organizacion_id UUID REFERENCES organizaciones(id) ON DELETE SET NULL,
    territorio VARCHAR(100),
    rol_situacional TEXT,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS situaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATE,
    fecha_fin DATE,
    territorio VARCHAR(100),
    organizacion_id UUID REFERENCES organizaciones(id) ON DELETE CASCADE,
    estado VARCHAR(50) DEFAULT 'ACTIVA'
);

CREATE TABLE IF NOT EXISTS senales_antropologicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fuente_id UUID REFERENCES fuentes(id) ON DELETE CASCADE,
    fecha_observacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_publicacion TIMESTAMP WITH TIME ZONE,
    contenido TEXT NOT NULL,
    fragmento_evidencia TEXT NOT NULL,
    tipo_enunciador VARCHAR(100) NOT NULL,
    actor_enunciador_id UUID REFERENCES actores(id) ON DELETE SET NULL,
    posicion_enunciador TEXT NOT NULL,
    situacion_id UUID REFERENCES situaciones(id) ON DELETE SET NULL,
    canal VARCHAR(100) NOT NULL,
    territorio VARCHAR(100),
    tema VARCHAR(100),
    tension_detectada TEXT,
    nivel_relevancia INTEGER DEFAULT 1,
    estado VARCHAR(50) DEFAULT 'CAPTURADA'
);

CREATE TABLE IF NOT EXISTS evidencias (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo VARCHAR(50) NOT NULL,
    contenido TEXT NOT NULL,
    fuente_id UUID REFERENCES fuentes(id) ON DELETE CASCADE,
    senal_id UUID REFERENCES senales_antropologicas(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES actores(id) ON DELETE SET NULL,
    situacion_id UUID REFERENCES situaciones(id) ON DELETE SET NULL,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    contexto TEXT,
    calidad INTEGER DEFAULT 5,
    trazabilidad VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS relaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_origen_id UUID REFERENCES actores(id) ON DELETE RESTRICT,
    actor_destino_id UUID REFERENCES actores(id) ON DELETE RESTRICT,
    tipo_relacion VARCHAR(100) NOT NULL,
    situacion_id UUID REFERENCES situaciones(id) ON DELETE CASCADE,
    descripcion TEXT,
    evidencia_id UUID REFERENCES evidencias(id) ON DELETE SET NULL,
    intensidad INTEGER DEFAULT 1,
    estado VARCHAR(50) DEFAULT 'ACTIVA'
);

CREATE TABLE IF NOT EXISTS practicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    actor_id UUID REFERENCES actores(id) ON DELETE SET NULL,
    situacion_id UUID REFERENCES situaciones(id) ON DELETE CASCADE,
    contexto TEXT,
    frecuencia VARCHAR(50),
    funcion TEXT,
    evidencia_id UUID REFERENCES evidencias(id) ON DELETE SET NULL,
    formalidad VARCHAR(50) DEFAULT 'INFORMAL'
);

CREATE TABLE IF NOT EXISTS rituales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    practica_id UUID REFERENCES practicas(id) ON DELETE CASCADE,
    funcion_social TEXT,
    funcion_organizacional TEXT,
    que_protege TEXT,
    nivel_institucionalizacion INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tensiones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    situacion_id UUID REFERENCES situaciones(id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    actor_a_id UUID REFERENCES actores(id) ON DELETE RESTRICT,
    actor_b_id UUID REFERENCES actores(id) ON DELETE RESTRICT,
    practica_implicada TEXT,
    discurso TEXT NOT NULL,
    practica_observada TEXT NOT NULL,
    tipo_tension VARCHAR(100),
    nivel_confianza DECIMAL(3,2) CHECK (nivel_confianza <= 1.00),
    estado VARCHAR(50) DEFAULT 'IDENTIFICADA'
);

CREATE TABLE IF NOT EXISTS deudas_culturales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    situacion_id UUID REFERENCES situaciones(id) ON DELETE CASCADE,
    practica_origen_id UUID REFERENCES practicas(id) ON DELETE SET NULL,
    ritual_id UUID REFERENCES rituales(id) ON DELETE SET NULL,
    problema_que_resuelve TEXT,
    costo_actual TEXT,
    funcion_que_preserva TEXT,
    nivel_deuda INTEGER DEFAULT 1,
    evidencia_id UUID REFERENCES evidencias(id) ON DELETE SET NULL,
    estado VARCHAR(50) DEFAULT 'ACTIVA'
);

CREATE TABLE IF NOT EXISTS patrones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    tipo_patron VARCHAR(100),
    nivel_recurrencia INTEGER DEFAULT 1,
    alcance VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'EN_CONSTRUCCION',
    confianza DECIMAL(3,2) CHECK (confianza <= 1.00)
);

CREATE TABLE IF NOT EXISTS hipotesis_antropologicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(20) UNIQUE NOT NULL,
    enunciado TEXT NOT NULL,
    patron_id UUID REFERENCES patrones(id) ON DELETE SET NULL,
    tension_id UUID REFERENCES tensiones(id) ON DELETE SET NULL,
    explicacion TEXT NOT NULL,
    evidencia_a_favor TEXT,
    evidencia_contra TEXT,
    nivel_confianza DECIMAL(3,2) CHECK (nivel_confianza <= 1.00),
    estado VARCHAR(50) DEFAULT 'PROPUESTA',
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_validacion TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS interpretaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evidencia_id UUID REFERENCES evidencias(id) ON DELETE CASCADE,
    interpretacion TEXT NOT NULL,
    autor VARCHAR(255) NOT NULL,
    principio_aplicado_id UUID REFERENCES principios_antropologicos(id) ON DELETE RESTRICT,
    confianza DECIMAL(3,2) CHECK (confianza <= 1.00),
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS principios_aplicados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principio_id UUID REFERENCES principios_antropologicos(id) ON DELETE RESTRICT,
    entidad_tipo VARCHAR(50) NOT NULL,
    entidad_id UUID NOT NULL,
    justificacion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS triangulaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hipotesis_id UUID REFERENCES hipotesis_antropologicas(id) ON DELETE CASCADE,
    evidencia_1_id UUID REFERENCES evidencias(id) ON DELETE RESTRICT,
    evidencia_2_id UUID REFERENCES evidencias(id) ON DELETE RESTRICT,
    evidencia_3_id UUID REFERENCES evidencias(id) ON DELETE RESTRICT,
    resultado TEXT NOT NULL,
    nivel_confianza DECIMAL(3,2) CHECK (nivel_confianza <= 1.00)
);

CREATE TABLE IF NOT EXISTS casos_antropologicos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organizacion_id UUID REFERENCES organizaciones(id) ON DELETE CASCADE,
    situacion_principal_id UUID REFERENCES situaciones(id) ON DELETE SET NULL,
    problema_inicial TEXT,
    tension_principal TEXT,
    deuda_cultural_principal_id UUID REFERENCES deudas_culturales(id) ON DELETE SET NULL,
    hipotesis_principal_id UUID REFERENCES hipotesis_antropologicas(id) ON DELETE SET NULL,
    nivel_madurez VARCHAR(50) DEFAULT 'INICIAL',
    estado VARCHAR(50) DEFAULT 'ABIERTO'
);

CREATE TABLE IF NOT EXISTS observaciones_etnograficas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    caso_id UUID REFERENCES casos_antropologicos(id) ON DELETE CASCADE,
    investigador_id UUID REFERENCES actores(id) ON DELETE RESTRICT,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    lugar TEXT,
    situacion TEXT,
    observacion TEXT NOT NULL,
    interpretacion_inicial TEXT,
    reflexividad TEXT,
    evidencia_id UUID REFERENCES evidencias(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reflexividad (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigador_id UUID REFERENCES actores(id) ON DELETE RESTRICT,
    caso_id UUID REFERENCES casos_antropologicos(id) ON DELETE CASCADE,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    posicion TEXT NOT NULL,
    supuesto TEXT NOT NULL,
    posible_sesgo TEXT,
    impacto_interpretacion TEXT
);

CREATE TABLE IF NOT EXISTS territorios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),
    pais VARCHAR(100) DEFAULT 'México',
    region VARCHAR(100),
    ciudad VARCHAR(100),
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS temporalidades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    inicio DATE,
    fin DATE,
    descripcion TEXT,
    evento_desencadenante TEXT
);
