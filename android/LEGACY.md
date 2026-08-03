# android/ — LEGADO

## Decisión de reconciliación (2026-08-02)

Esta carpeta (`android/`, paquete `com.laboratorio.antrosapiens`) es un shell
**WebView** que cargaba el dashboard del laboratorio web en
`https://lemures-66.vercel.app/lab/dashboard`.

**El APK de Antrosapiens ya NO se produce aquí.** La fuente de verdad del APK es
la app 100% nativa:

- Repo: `~/antrosapiens` (RadarHD · Motor B)
- Paquete: `com.hamcadigital.antrosapiens`
- Stack: Kotlin + Jetpack Compose + MVVM + Clean Architecture
  (Room · DataStore · Koin 4 · OkHttp+Jsoup · Navigation Compose)
- CI: `.github/workflows/build-apk.yml` (`assembleDebug` + `bundleRelease` + tests)

Motivos:
- La nativa es offline-first (radar y peritaje con DB local) y no depende de la
  disponibilidad de un servidor remoto.
- El shell WebView no aporta datos ni funcionalidad propia: era una página web
  enmascarada de app.
- El acceso al laboratorio web se cubre desde la app nativa abriendo la URL en
  el navegador del sistema (`ACTION_VIEW`), sin WebView embebido.

## Estado

- Workflow `build-antrosapiens-apk.yml` **eliminado** (el APK solo lo publica la
  app nativa).
- Esta carpeta se conserva como referencia de exploración histórica; no debe
  volver a ser fuente de artefactos de release.
