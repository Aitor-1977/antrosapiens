# sandbox/ — cuarentena

Scripts experimentales sueltos que estaban en la raíz del repo, movidos aquí el
2026-09-02 al preparar la arquitectura multifuente (Entrega 4).

**No forman parte del motor.** No se ejecutan desde el pipeline, el scheduler ni
la API, y `pytest` no los recoge (`pytest.ini` fija `testpaths = tests`). Esta
carpeta está en `.gitignore`.

## Por qué están aislados

Varios violan la **frontera Motor A / Motor B** declarada en `CLAUDE.md`
(el repo extrae y normaliza; nunca interpreta ni decide acción comercial):

| Script | Problema |
|---|---|
| `aplicar_filtro.py` | Infiere `tensión` / `actores` / "Alerta Cultural" leyendo titulares. |
| `concentrador.py` | Señales sintéticas hardcodeadas; declara "CASO CANDIDATO" solo. |
| `priorizador.py` | Score inventado fuera de reglas declaradas ("Tensión validada"). |
| `acercamiento.py` | Genera acción comercial ("AGENDAR LLAMADA… $210,000 MXN") — Motor C. |
| `pipeline_captura.py`, `motor_epistemico.py` | Escriben en Neon productivo con `tipo_tension="DEUDA_CULTURAL"`, `nivel_confianza 0.90` hardcodeado. |
| `motor_antro.py` | Escribe hipótesis antropológica en `antrolab.db`. |
| `seed_antrolab.py` | Semilla de un esquema divergente (`evidencia_raw`, `observacion_antropologica`). |
| `test_db.py`, `test_imp.py` | Smoke tests sueltos; `test_db.py` importa `psycopg2` y rompía la colección de pytest. |

El equivalente **gobernado** de "concentrar evidencia" y "densidad" vive ahora en
`hd_scraper/concentrador.py` (determinista, sin interpretación, sin escritura en
producción).

Si algo de aquí se necesita de verdad, se reescribe como módulo de `hd_scraper/`
con su test y, si toca interpretación, con la ampliación previa de `CLAUDE.md`.
