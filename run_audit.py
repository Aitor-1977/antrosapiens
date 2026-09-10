import sys
import traceback
from hd_scraper.db.database import get_db
from hd_scraper.promocion_store import promover_lote

OUT = "/data/data/com.termux/files/home/antrosapiens/audit_result.txt"

def main():
    db = get_db()
    rep = promover_lote(db, aplicar=True)

    counts = {}
    for tabla in ("expedientes_candidatos", "evidencias", "prospectos", "evidencia_clasificada"):
        try:
            r = db.fetch_one("SELECT COUNT(*) AS n FROM " + tabla)
            counts[tabla] = r["n"] if r else 0
        except Exception as e:
            counts[tabla] = "ERR:%s" % e

    estados = {}
    r = db.fetch_all("SELECT estado, COUNT(*) AS n FROM expedientes_candidatos GROUP BY estado")
    for row in r:
        estados[row["estado"]] = row["n"]

    lines = []
    lines.append("=== PROMOCION DE CANDIDATOS (APLICADO) ===")
    lines.append("evaluados : %s" % rep["evaluados"])
    lines.append("promovidos: %s" % rep["promovidos"])
    lines.append("")
    lines.append("detalle:")
    for d in rep["detalle"]:
        marca = "PROMUEVE" if d["promovido"] else "queda abierto"
        lines.append("  [%s] %s (categoria=%s) -> %s" % (
            d["expediente_id"], d["organizacion"], d["categoria"] or "-", marca))
        lines.append("      tipos: %s" % (d["tipos_encontrados"] or "(ninguno)"))
        lines.append("      razon: %s" % d["razon"])
    lines.append("")
    lines.append("=== CONTEO REAL DE LA BASE DE DATOS ===")
    for k, v in counts.items():
        lines.append("%s: %s" % (k, v))
    lines.append("")
    lines.append("=== ESTADO expedientes ===")
    for k, v in estados.items():
        lines.append("%s: %s" % (k, v))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("EXC: %r\n" % e)
            f.write(traceback.format_exc())
