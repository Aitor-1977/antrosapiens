# Capa 05 — Enriquecimiento

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Resolver sitio oficial, discurso corporativo, vertical y contacto.
- **Problema que resuelve:** La evidencia gana valor con contexto (web oficial, tesis, decisor).
- **Arquitectura:** Resolución multi-estrategia con niveles de confianza; Wikidata con caché.

## Componentes (archivos)
hd_scraper/enrich.py, hd_scraper/contacto.py, hd_scraper/directorio.py, hd_scraper/hunter.py

## Endpoints
POST /enrich, POST /verificar-contacto, POST /directorio

## Tablas
directorio_cache

## Funciones
resolver_sitio, extraer_discurso, sugerir_vertical, enriquecer, rutas_contacto, dominio_de

## Entradas → Salidas
- **Entradas:** Nombre de la entidad
- **Salidas:** Sitio (candidato con confianza), discurso, vertical, enlaces, contacto

## Dependencias
← C4 · → C10

## Tests
test_enrich, test_contacto, test_directorio, test_hunter

## Criterios de aceptación
El sitio es un CANDIDATO con nivel de confianza; LinkedIn no se raspa (solo enlace).

## Limitaciones
Hunter es opcional (requiere HUNTER_API_KEY).

## Relación con otras capas
Aporta 'thick data' a prospectos y a la curaduría.
