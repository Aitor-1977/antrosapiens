plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.hamacadigital.antrosapiens.v2"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.hamacadigital.antrosapiens.v2"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }
}

// --- BUILD ID embebido en el APK ---
// Genera src/main/assets/public/build_info.js en TIEMPO DE COMPILACIÓN (no en
// tiempo de ejecución) con un identificador de build automático. El HTML lo
// consume vía window.BUILD_ID. El archivo es generado, no se commite.
val generateBuildId by tasks.registering {
    val outFile = layout.projectDirectory.file("src/main/assets/public/build_info.js")
    // Entrada cambiante en cada build => siempre se regenera el BUILD ID.
    inputs.property("buildInstant", System.currentTimeMillis().toString())
    outputs.file(outFile)
    doLast {
        val gitHash = try {
            val proc = ProcessBuilder("git", "rev-parse", "--short", "HEAD")
                .directory(project.projectDir)
                .redirectErrorStream(true)
                .start()
            val out = proc.inputStream.bufferedReader().readText().trim()
            proc.waitFor()
            if (out.isNotBlank()) out else "nogit"
        } catch (e: Exception) {
            "nogit"
        }
        // Confiable sin dependencias de java.* (no disponibles en el classpath del script Kotlin DSL).
        val ts = System.currentTimeMillis().toString()
        val buildId = "v1-${gitHash}-${ts}"
        outFile.asFile.parentFile.mkdirs()
        outFile.asFile.writeText(
            "// Generado automáticamente en tiempo de compilación. NO editar manualmente.\n" +
            "window.BUILD_ID = \"${buildId}\";\n"
        )
        println("BUILD_ID generado: ${buildId}")
    }
}

// --- Token de ingesta embebido en el APK (búsqueda en vivo) ---
// AntrolabsHD es una herramienta de un solo operador (Mario): el mismo
// X-Ingest-Token que ya protege /scrape, /investigacion y el resto de la
// intake (ver hd_scraper/api/app.py:_exigir_token) se embebe en SU PROPIO
// build para que la app pueda disparar una búsqueda real (POST /scrape)
// en vez de solo leer lo que ya hay en Neon. Nunca se commitea un token
// real: esta tarea lee HD_INGEST_TOKEN de (en orden) una property de
// Gradle (-PHD_INGEST_TOKEN=...), local.properties (gitignored, igual que
// sdk.dir) o la variable de entorno del mismo nombre; sin ninguna,
// window.HD_INGEST_TOKEN queda "" y la app sigue funcionando en modo
// solo-lectura (igual que hasta ahora), sin romperse.
val generateHdConfig by tasks.registering {
    val outFile = layout.projectDirectory.file("src/main/assets/public/hd_config.js")
    val localProps = java.util.Properties()
    val localPropsFile = rootProject.file("local.properties")
    if (localPropsFile.exists()) {
        localPropsFile.inputStream().use { localProps.load(it) }
    }
    val token = (project.findProperty("HD_INGEST_TOKEN") as String?)
        ?: localProps.getProperty("HD_INGEST_TOKEN")
        ?: System.getenv("HD_INGEST_TOKEN")
        ?: ""
    // No se registra el valor como input (solo si está presente o no): un
    // cambio de token no debe filtrarse a los logs de Gradle.
    inputs.property("hdIngestTokenPresente", token.isNotBlank())
    outputs.file(outFile)
    doLast {
        outFile.asFile.parentFile.mkdirs()
        outFile.asFile.writeText(
            "// Generado en tiempo de compilación. NO editar a mano.\n" +
            "// NO commitear: este archivo está en .gitignore precisamente porque\n" +
            "// puede contener el token real de intake.\n" +
            "window.HD_INGEST_TOKEN = \"${token}\";\n"
        )
        println(
            if (token.isBlank())
                "HD_INGEST_TOKEN no configurado: búsqueda en vivo deshabilitada en este build (modo solo-lectura)."
            else
                "HD_INGEST_TOKEN configurado: búsqueda en vivo habilitada en este build."
        )
    }
}

tasks.named("preBuild") { dependsOn(generateBuildId, generateHdConfig) }

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    // WebViewAssetLoader: sirve los assets bajo un origen https real y
    // autorizable por CORS, en lugar de file:// (origen `null`).
    implementation("androidx.webkit:webkit:1.11.0")
}
