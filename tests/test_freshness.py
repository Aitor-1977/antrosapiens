"""score_freshness (2026-09-20): antigüedad de la evidencia primaria, gate de
visibilidad de /verificados. Función pura, sin BD."""
import datetime as _dt

from hd_scraper.freshness import score_freshness


def test_hoy_vale_100():
    hoy = _dt.date(2026, 9, 20)
    assert score_freshness(hoy.isoformat(), hoy=hoy) == 100


def test_90_dias_vale_50():
    hoy = _dt.date(2026, 9, 20)
    hace_90 = (hoy - _dt.timedelta(days=90)).isoformat()
    assert score_freshness(hace_90, hoy=hoy) == 50


def test_180_dias_o_mas_vale_0():
    hoy = _dt.date(2026, 9, 20)
    hace_180 = (hoy - _dt.timedelta(days=180)).isoformat()
    hace_400 = (hoy - _dt.timedelta(days=400)).isoformat()
    assert score_freshness(hace_180, hoy=hoy) == 0
    assert score_freshness(hace_400, hoy=hoy) == 0


def test_sin_fecha_no_fechado_vale_0_no_100():
    assert score_freshness(None) == 0
    assert score_freshness("") == 0


def test_fecha_invalida_vale_0():
    assert score_freshness("no-es-una-fecha") == 0


def test_acepta_timestamp_iso_completo_no_solo_fecha():
    hoy = _dt.date(2026, 9, 20)
    assert score_freshness(f"{hoy.isoformat()}T10:00:00Z", hoy=hoy) == 100
