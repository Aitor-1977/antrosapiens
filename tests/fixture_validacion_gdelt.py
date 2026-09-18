"""FIXTURE CONGELADO — validación retrospectiva de GDELT (Fase 1).

Definido ANTES de releer `hd_scraper/connectors/gdelt.py` o
`tests/test_gdelt.py` en esta tarea (GdeltConnector ya existe y ya está en
producción desde 2026-09-04 — esto NO es una integración nueva, ver
discrepancia reportada y resuelta por Mario: Opción 1 + Opción 2).

Consulta de prueba: "Nowports" (logística/freight, México). Elegida por
estar ya declarada en `seed_prospectos.py` con `categoria="Startup"` — NO
está en la lista de organizaciones reclasificadas "Corporativo"
(Nubank/Rappi/Kavak/Bitso/Clip/Konfío/Ualá), que quedarían excluidas de
promoción sin importar la evidencia (`promocion_candidatos.CATEGORIA_EXCLUIDA`).

Diferencia deliberada con el fixture del contrato de /verificados (Fase 1.5
del PR #22): aquel describía un dato SINTÉTICO, bajo control total, así que
podía fijar un valor literal exacto. GDELT es una fuente EXTERNA y VIVA: no
puedo predecir el titular exacto que devolverá hoy. Este fixture fija,
antes de ver el resultado real:
  (a) la FORMA y los TIPOS que cualquier evidencia de GDELT debe cumplir
      (esto sí es una expectativa dura, verificable campo por campo);
  (b) el resultado MEJOR CASO en /verificados si la nota real resulta tener
      una autodeclaración o huella práctica identificable;
  (c) que un resultado real 'contextual'/'corroborante' (sin autodeclaración)
      es una salida VÁLIDA del pipeline, no una falla de GDELT ni del
      clasificador — simplemente esa nota no promueve, igual que le pasaría
      a cualquier nota de prensa de cualquier otro conector.
"""
from __future__ import annotations

QUERY_PRUEBA = "Nowports"

# (a) Forma y tipos esperados de CUALQUIER evidencia cruda que GDELT escriba
# para esta consulta — verificable sin importar qué titular real traiga hoy.
EXPECTATIVA_EVIDENCIA_CRUDA_GDELT = {
    "connector": "gdelt",
    "origen_declaracion": "prensa",  # GDELT indexa notas de prensa, no autodeclaraciones directas
    "empresa_mencionada": QUERY_PRUEBA,  # estructural: el término de la consulta, no inferido
    "persona_citada": None,  # GDELT ArtList no lo provee de forma estructural (confirmado en código)
    "cargo": None,           # ídem
    # No fijos, pero con tipo/forma obligatoria:
    "cita_textual": "str no vacío, debe mencionar 'Nowports'",
    "url_fuente": "str, debe empezar con http:// o https://",
    "nombre_medio": "str no vacío",
    "fecha_publicacion": "str ISO 8601 o None (no_fechado)",
    "tipo_evento": "el declarado en QuerySpec por quien lanza la búsqueda, no inferido",
    "hash_dedup": "str, sha256(empresa + URL normalizada)",
}

# (b) MEJOR CASO en /verificados (11 campos del contrato canónico,
# schema_expediente.ExpedienteVerificado) — solo se cumple si la nota real
# de hoy trae una autodeclaración o huella práctica identificable.
EXPECTATIVA_EXPEDIENTE_VERIFICADO_MEJOR_CASO = {
    "organizacion": "Nowports",
    "categoria": "Startup",  # ya declarado en seed_prospectos.py, autoridad estructural
    "tipo_epistemologico": "senal_primaria_autodeclaracion o senal_primaria_huella_practica (los únicos que promueven)",
    "cita_textual": "str real, no vacío",
    "url_fuente": "str real, http(s)",
    "nombre_medio": "str real, no vacío",
    "fecha_publicacion": "str ISO 8601 o None",
    "persona_citada": None,   # GDELT nunca lo declara estructuralmente
    "cargo": None,            # ídem
    "enunciador_nombre": "str o None, según si el texto real trae un nombre identificable",
    "enunciador_cargo": "str o None, según si el texto real trae un cargo identificable",
}

# (c) Resultado alternativo VÁLIDO (no es una falla): la nota real es
# 'contextual' o 'corroborante' -> nunca aparece en /verificados. Si esto
# ocurre con "Nowports", Fase 3 debe probar con otra organización antes de
# concluir nada sobre GDELT en sí.
RESULTADO_SIN_PROMOCION_ES_VALIDO = True
