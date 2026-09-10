// Configuración de plugins a nivel de proyecto raíz. Las versiones se declaran
// aquí y se aplican en cada módulo (:app) con `apply false`.
plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
    // Chaquopy retirado: la prospección consume el Motor A remoto (Vercel), no un
    // motor Python embebido. La app es un cliente del backend publicado.
}
