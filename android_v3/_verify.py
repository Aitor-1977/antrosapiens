import zipfile, hashlib, os
apk="app/build/outputs/apk/debug/app-debug.apk"
z=zipfile.ZipFile(apk)
cands=[n for n in z.namelist() if n.lower().endswith("index.html")]
lines=[]
lines.append("assets index.html en APK: "+str(cands))
for c in cands:
    data=z.read(c)
    lines.append("ruta interna: "+c)
    lines.append("sha256 interno: "+hashlib.sha256(data).hexdigest())
src="app/src/main/assets/public/index.html"
with open(src,"rb") as fh: s=fh.read()
lines.append("fuente: "+src)
lines.append("sha256 fuente: "+hashlib.sha256(s).hexdigest())
lines.append("COINCIDEN: "+str(hashlib.sha256(data).hexdigest()==hashlib.sha256(s).hexdigest()))
with open("/data/data/com.termux/files/home/antrosapiens/android_v3/_verify_out.txt","w") as out:
    out.write("\n".join(lines))
