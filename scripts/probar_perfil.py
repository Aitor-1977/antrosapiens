"""CLI para validar EN VIVO el extractor de perfil fundacional (fuente orgánica).

Corre contra el sitio PROPIO de una organización (no prensa) y muestra el thick
data estructural extraído: escala/tamaño, año de fundación y descripción. Pensado
para que el operador valide la extracción profunda en su entorno (donde la red no
está bloqueada).

Uso:
    python -m scripts.probar_perfil "Nubank" nubank.com.mx
    python -m scripts.probar_perfil "Y Combinator" ycombinator.com

Salida: JSON con el perfil. `escala` siempre presente ('indeterminada' si el
sitio no declara tamaño).
"""
from __future__ import annotations

import argparse
import json

from hd_scraper.perfil_fundacional import construir_perfil


def main() -> None:
    ap = argparse.ArgumentParser(description="Extrae el perfil fundacional desde la fuente orgánica.")
    ap.add_argument("empresa", help="Nombre de la organización")
    ap.add_argument("dominio", help="Dominio propio (p. ej. nubank.com.mx)")
    args = ap.parse_args()

    perfil = construir_perfil(args.empresa, args.dominio)
    print(json.dumps({
        "empresa": perfil.empresa,
        "escala": perfil.escala,
        "anio_fundacion": perfil.anio_fundacion,
        "url_perfil": perfil.url_perfil,
        "fuente_discurso": perfil.fuente_discurso,
        "discurso_corporativo": (perfil.discurso_corporativo or "")[:400],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
