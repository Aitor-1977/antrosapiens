import org.gradle.api.plugins.ExtensionAware
import com.chaquo.python.PythonExtension

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.laboratorio.antrosapiens"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.laboratorio.antrosapiens"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        (this as ExtensionAware).extensions.getByName<PythonExtension>("python").pip.apply {
            install("fastapi")
            install("uvicorn")
            install("httpx")
            install("feedparser")
            install("python-dateutil")
            install("beautifulsoup4")
            install("apscheduler")
        install("pydantic<2")
        }

        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")
        }
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

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
}
