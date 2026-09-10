from hd_scraper.db.database import get_db
with open("/data/data/com.termux/files/home/antrosapiens/imp1.txt","w") as f:
    f.write("import ok\n")
try:
    from hd_scraper.promocion_store import promover_lote
    with open("/data/data/com.termux/files/home/antrosapiens/imp1.txt","a") as f:
        f.write("promover_lote ok\n")
except Exception as e:
    with open("/data/data/com.termux/files/home/antrosapiens/imp1.txt","a") as f:
        f.write("ERR promover_lote: %r\n" % e)
