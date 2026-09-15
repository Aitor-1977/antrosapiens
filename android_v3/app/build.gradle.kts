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

tasks.named("preBuild") { dependsOn(generateBuildId) }

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    // WebViewAssetLoader: sirve los assets bajo un origen https real y
    // autorizable por CORS, en lugar de file:// (origen `null`).
    implementation("androidx.webkit:webkit:1.11.0")
}
