// Configuración de plugins a nivel de proyecto raíz. Las versiones se declaran
// aquí y se aplican en cada módulo (:app) con `apply false`.
plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
    id("com.chaquo.python") version "15.0.1" apply false
    // Chaquopy: ejecuta el motor Python de AntroSapiens (hd-scraper) dentro de la
    // APK, reutilizando los motores reales de captura/validación sin reescribirlos.
}
