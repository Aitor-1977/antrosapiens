# Capa 00 — Captura e Ingesta

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Traer señales públicas crudas de fuentes externas.
- **Problema que resuelve:** La evidencia vive dispersa en prensa, feeds y job boards; hay que capturarla sin interpretarla.
- **Arquitectura:** Conectores intercambiables (search/fetch/normalize/validate) + ingesta gratuita (RSS/YouTube) que emite al webhook.

## Componentes (archivos)
hd_scraper/connectors/{base,google_news,gdelt,rss_fijos,job_boards}.py, hd_scraper/ingesta/{noticias,youtube,webhook}.py, hd_scraper/signals.py

## Endpoints
POST /webhook/ingesta, POST /ingesta/noticias, GET /senales-capa0

## Tablas
senales_capa0

## Funciones
connector.search/fetch/normalize, detectar_keywords, calcular_confianza, fuente_confiable

## Entradas → Salidas
- **Entradas:** QuerySpec (empresa, tipo_evento, categoría)
- **Salidas:** RawItem crudos + señales Capa 0

## Dependencias
→ Capa 1 (Normalización)

## Tests
test_google_news, test_gdelt, test_rss_fijos, test_job_boards, test_ingesta_connectors, test_signals

## Criterios de aceptación
Un 404 de job board = 'slug no está', no cuenta como fallo; salud por sub-fuente.

## Limitaciones
El proxy de egress puede bloquear news.google.com / api.gdeltproject.org.

## Relación con otras capas
Alimenta a C1/C2; salud gestionada por governance/.
