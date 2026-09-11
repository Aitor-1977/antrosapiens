"""Componente 1 del cierre de 15: la arquitectura del Motor Epistémico de
Capa 0 separa evidencia / clasificación / expediente / candidato /
interpretación en piezas explícitas y desacopladas:

    evidencia (evidencias)
      -> clasificación (clasificacion_epistemologica.py, evidencia_clasificada)
      -> expediente (expedientes_candidatos)
      -> candidato (candidato.py, tabla candidatos — puente BC-I<->BC-II)
      -> interpretación (RadarHD, fuera de este repo — ver CLAUDE.md
         "Frontera Motor A / Motor B")

Este test fija esa separación como comportamiento verificable: cada capa
vive en su propio módulo/tabla, ninguna de las capas de Motor A importa
maquinaria de IA/LLM (salvo `nvidia_parser.py`, que es síntesis opcional y
siempre con fallback determinista, no clasificación), y clasificación no
promueve, ni expediente decide comercialmente.
"""
import ast
from pathlib import Path

from hd_scraper import candidato, clasificacion_epistemologica, clasificacion_store
from hd_scraper import promocion_candidatos, promocion_store

_HD_SCRAPER = Path(__file__).resolve().parent.parent / "hd_scraper"

# Módulos de Motor A que NO deben depender de un LLM/IA para su función
# propia (evidencia, clasificación, expediente, candidato). La síntesis
# opcional con NVIDIA (Capa 19) es una pieza aparte, deliberadamente distinta,
# con fallback determinista garantizado — no se incluye aquí.
_MODULOS_SIN_IA = (
    clasificacion_epistemologica,
    clasificacion_store,
    promocion_candidatos,
    promocion_store,
    candidato,
)

_MARCADORES_IA = ("openai", "anthropic", "nvidia", "llm", "gpt", "claude")


def _imports_del_modulo(modulo) -> set[str]:
    archivo = Path(modulo.__file__)
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(n.name for n in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
    return nombres


def test_capas_de_motor_a_no_importan_maquinaria_de_ia():
    for modulo in _MODULOS_SIN_IA:
        imports = _imports_del_modulo(modulo)
        for nombre in imports:
            bajo = nombre.lower()
            for marcador in _MARCADORES_IA:
                assert marcador not in bajo, (
                    f"{modulo.__name__} importa {nombre!r}, que sugiere "
                    f"dependencia de IA/LLM ({marcador!r}) — Capa 0 debe ser "
                    "determinista y auditable")


def test_evidencia_es_capa_de_extraccion_sin_juicio():
    """`evidencias` no tiene ninguna columna de interpretación (score, deuda,
    icp): eso vive en RadarHD (Motor B), no aquí. Contrato de datos, ver
    CLAUDE.md."""
    schema = (_HD_SCRAPER / "db" / "schema.sql").read_text(encoding="utf-8")
    inicio = schema.index("CREATE TABLE IF NOT EXISTS evidencias")
    fin = schema.index(");", inicio)
    bloque_evidencias = schema[inicio:fin].lower()
    for prohibido in ("deuda_cultural", "score_icp", "icp_score", "juicio"):
        assert prohibido not in bloque_evidencias


def test_clasificacion_no_decide_promocion():
    """clasificacion_store.guardar_clasificacion escribe SIEMPRE estado
    'abierto': la transición a 'candidato' es responsabilidad exclusiva de
    promocion_store, una capa distinta."""
    assert clasificacion_store.ESTADO_INICIAL == "abierto"


def test_candidato_es_capa_distinta_de_clasificacion_y_promocion():
    """candidato.py no importa ni reimplementa la cascada de clasificación ni
    la regla de promoción: solo referencia sus resultados ya calculados
    (organización -> candidato -> prospecto -> expediente -> evidencia)."""
    imports = _imports_del_modulo(candidato)
    assert not any("clasificacion_epistemologica" in n for n in imports)
    assert not any("promocion_candidatos" in n for n in imports)


def test_interpretacion_deuda_cultural_no_vive_en_motor_a():
    """Ningún módulo de la cadena evidencia->clasificación->expediente->
    candidato produce campos de salida de tipo Deuda Cultural™ (eso es
    RadarHD, Motor B). Se comprueba sobre los campos de SALIDA reales
    (TIPOS y los campos de los dataclasses), no sobre el texto completo del
    módulo — los docstrings SÍ nombran "Deuda Cultural™" para documentar
    justamente que está fuera de su frontera, y eso es legítimo."""
    assert clasificacion_epistemologica.TIPOS == (
        "senal_primaria_autodeclaracion", "senal_primaria_huella_practica",
        "corroborante", "contextual",
    )
    campos_clasificacion = {
        f.name for f in clasificacion_epistemologica.Clasificacion.__dataclass_fields__.values()
    }
    campos_enunciador = {
        f.name for f in clasificacion_epistemologica.Enunciador.__dataclass_fields__.values()
    }
    for campo in campos_clasificacion | campos_enunciador:
        assert "deuda" not in campo.lower()
