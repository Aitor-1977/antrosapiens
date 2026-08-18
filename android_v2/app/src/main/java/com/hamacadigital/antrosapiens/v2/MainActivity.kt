package com.hamacadigital.antrosapiens.v2

import android.annotation.SuppressLint
import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.ViewGroup
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.InetSocketAddress
import java.net.Socket

/**
 * AntrolabsHD V2 — Radar real (FASE C).
 *
 * Arranca el backend real de hd-scraper (Motor A) embebido en la APK vía
 * Chaquopy, exponiéndolo en http://127.0.0.1:8000, y carga la pantalla
 * funcional del Radar (assets/public/index.html) que consome esos endpoints
 * reales. La base SQLite local se siembra con el directorio curado de LATAM.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView

    companion object {
        private const val TAG = "AntrolabsHD"
        private const val API_HOST = "127.0.0.1"
        private const val API_PORT = 8000
        private const val READY_TIMEOUT_MS = 20_000L
        private const val READY_POLL_MS = 500L
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // El backend (FastAPI/Uvicorn embebido vía Chaquopy) debe arrancar y
        // quedar listo ANTES de cargar el WebView: si no está escuchando en
        // 127.0.0.1:8000 el primer fetch de la UI falla con "Failed to fetch".
        iniciarBackend()

        val fondo = Color.parseColor("#FCFAED")

        WebView.setWebContentsDebuggingEnabled(true)

        web = WebView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccessFromFileURLs = true
            settings.allowUniversalAccessFromFileURLs = true
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            // El backend corre en http://127.0.0.1 (claro): permitir mixto.
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            setBackgroundColor(fondo)

            webChromeClient = object : WebChromeClient() {
                override fun onConsoleMessage(consoleMessage: ConsoleMessage): Boolean {
                    Log.e("HD_CONSOLE", consoleMessage.message() + " -- línea " + consoleMessage.lineNumber() + " de " + consoleMessage.sourceId())
                    return true
                }
            }

            webViewClient = object : WebViewClient() {
                override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                    super.onReceivedError(view, request, error)
                    Log.e("HD_NET_ERROR", "URL: " + (request?.url) + " -- Error: " + (error?.description))
                }
            }
        }

        setContentView(web)
        web.loadUrl("file:///android_asset/public/index.html")
    }

    /**
     * Inicia Chaquopy y el servidor local del backend RadarHD (idempotente) y
     * espera a que escuche en 127.0.0.1:8000 antes de devolver el control.
     * Cualquier fallo del motor Python se registra en Logcat (tag AntrolabsHD)
     * para poder diagnosticar "Failed to fetch" / "Backend no disponible".
     */
    private fun iniciarBackend() {
        if (!Python.isStarted()) {
            Log.i(TAG, "Arrancando runtime de Chaquopy…")
            try {
                Python.start(AndroidPlatform(this))
                Log.i(TAG, "Runtime de Chaquopy iniciado.")
            } catch (e: Exception) {
                Log.e(TAG, "FALLO al iniciar Chaquopy: ${e.message}", e)
                return
            }
        }

        try {
            val py = Python.getInstance()
            Log.i(TAG, "Invocando server.start_server(filesDir=${filesDir.absolutePath})…")
            val resultado = py.getModule("server").callAttr("start_server", filesDir.absolutePath)
            // start_server devuelve un dict Python: {"ok": bool, "error": str?}
            val ok = resultado?.get("ok")?.toBoolean() ?: false
            val error = resultado?.get("error")?.toString()
            if (ok) {
                Log.i(TAG, "server.start_server devolvió ok=true (host=$API_HOST puerto=$API_PORT).")
            } else {
                Log.e(TAG, "server.start_server devolvió ok=false. Motivo del motor Python: ${error ?: "desconocido"}")
            }
        } catch (e: Exception) {
            // El arranque del backend no debe tumbar la app, pero sí debemos
            // dejar rastro exacto del fallo en el motor Python.
            Log.e(TAG, "EXCEPCIÓN al invocar server.start_server: ${e.message}", e)
        }

        esperarServidorListo()
    }

    /** Sondea 127.0.0.1:API_PORT hasta que acepta conexiones o agota el timeout. */
    private fun esperarServidorListo() {
        val deadline = System.currentTimeMillis() + READY_TIMEOUT_MS
        var intentos = 0
        while (System.currentTimeMillis() < deadline) {
            intentos++
            if (puertoAbierto()) {
                Log.i(TAG, "Servidor local LISTO en http://$API_HOST:$API_PORT (intento $intentos).")
                return
            }
            try {
                Thread.sleep(READY_POLL_MS)
            } catch (_: InterruptedException) {
                Thread.currentThread().interrupt()
                break
            }
        }
        Log.e(TAG, "TIMEOUT ($READY_TIMEOUT_MS ms, $intentos intentos): el servidor local NO está escuchando en http://$API_HOST:$API_PORT. La UI mostrará 'Backend no disponible'.")
    }

    /** Comprobación TCP liviana de que el puerto del backend acepta conexiones. */
    private fun puertoAbierto(): Boolean {
        return try {
            Socket().use { s ->
                s.connect(InetSocketAddress(API_HOST, API_PORT), 300)
                true
            }
        } catch (_: Exception) {
            false
        }
    }

    override fun onBackPressed() {
        if (web.canGoBack()) {
            web.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
