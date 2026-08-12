import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import os.path, sys as _sys, time

HOME = os.path.expanduser("~")
proj = os.path.join(HOME, "antrosapiens")
_sys.path.insert(0, proj)

from hd_scraper.connectors.gdelt import GdeltConnector
from hd_scraper.db.database import Database
from hd_scraper.db.models import QuerySpec
from hd_scraper.governance.rate_limit import RateLimiter
from hd_scraper.pipeline import run_connector

ORGS = sys.argv[1:] if len(sys.argv) > 1 else [
    "Cobre", "Mercado Libre", "Rappi", "Cometa",
]

db = Database()
db.init_schema()

rl = RateLimiter("gdelt", min_interval_s=12.0, max_retries=5, backoff_base_s=5.0)

for org in ORGS:
    query = QuerySpec(empresa=org, tipo_evento="ronda")
    try:
        with GdeltConnector(rate_limiter=rl) as connector:
            res = run_connector(db, connector, query)
        print(f"gdelt[{org}] {res.resumen()}")
    except Exception as e:
        print(f"gdelt[{org}] ERR {type(e).__name__}: {str(e)[:120]}")
    time.sleep(3)

db.close()
print("DONE")
