#!/usr/bin/env bash
#
# build-apk.sh — Compila el APK de la app Android V2 (AntrolabsHD)
#
# Paquete / applicationId: com.hamacadigital.antrosapiens.v2
# Proyecto Gradle:         android_v2/
#
# Uso:
#   scripts/build-apk.sh                 # assembleDebug
#   scripts/build-apk.sh debug           # assembleDebug   (explícito)
#   scripts/build-apk.sh release         # assembleRelease (requiere firma)
#   BUILD_TYPE=release scripts/build-apk.sh
#
# El script localiza el SDK de Android (ANDROID_HOME / ANDROID_SDK_ROOT o
# local.properties) y delega en el Gradle wrapper del módulo android_v2.
set -euo pipefail

# --- Resolución de rutas -----------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${PROJECT_ROOT}/android_v2"

if [ ! -d "${APP_DIR}" ]; then
    echo "ERROR: no se encuentra el proyecto ${APP_DIR}" >&2
    exit 1
fi

BUILD_TYPE="${1:-${BUILD_TYPE:-debug}}"
case "${BUILD_TYPE}" in
    debug|release) ;;
    *)
        echo "ERROR: BUILD_TYPE inválido '${BUILD_TYPE}' (usa debug|release)" >&2
        exit 1
        ;;
esac

# --- Resolución del Android SDK ---------------------------------------------
if [ -n "${ANDROID_HOME:-}" ]; then
    SDK_DIR="${ANDROID_HOME}"
elif [ -n "${ANDROID_SDK_ROOT:-}" ]; then
    SDK_DIR="${ANDROID_SDK_ROOT}"
elif [ -f "${APP_DIR}/local.properties" ]; then
    SDK_DIR="$(grep -E '^sdk.dir=' "${APP_DIR}/local.properties" | cut -d'=' -f2-)"
fi

if [ -n "${SDK_DIR:-}" ] && [ -d "${SDK_DIR}" ]; then
    export ANDROID_HOME="${SDK_DIR}"
    export ANDROID_SDK_ROOT="${SDK_DIR}"
    echo "Android SDK: ${SDK_DIR}"
else
    echo "ADVERTENCIA: Android SDK no detectado (ANDROID_HOME / local.properties)." >&2
    echo "El build fallará si Gradle no puede ubicar el SDK." >&2
fi

# --- Compilación -------------------------------------------------------------
cd "${APP_DIR}"

GRADLEW=./gradlew
if [ ! -x "${GRADLEW}" ]; then
    chmod +x "${GRADLEW}"
fi

echo "==> Compilando ${BUILD_TYPE} de android_v2 (com.hamacadigital.antrosapiens.v2)"
"${GRADLEW}" clean "assemble$(printf '%s' "${BUILD_TYPE}" | tr '[:lower:]' '[:upper:]')"

# --- Localización del artefacto ----------------------------------------------
APK_PATTERN="${APP_DIR}/app/build/outputs/apk/${BUILD_TYPE}/*-${BUILD_TYPE}.apk"
APK="$(ls -1 ${APK_PATTERN} 2>/dev/null | head -n1 || true)"

if [ -z "${APK}" ]; then
    echo "ERROR: no se encontró el APK generado en ${APP_DIR}/app/build/outputs/apk/" >&2
    exit 1
fi

echo "==> APK generado:"
echo "    ${APK}"
echo "    $(du -h "${APK}" | cut -f1)"
