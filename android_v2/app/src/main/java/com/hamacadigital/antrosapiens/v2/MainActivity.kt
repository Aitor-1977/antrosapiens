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
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader

/**
 * AntrolabsHD V2 — cliente del Radar.
 *
 * La app es un cliente del Motor A **remoto** (antrosapiens-api-pro): no
 * embebe intérprete Python ni levanta servidor local. Carga la pantalla del
 * Radar (assets/public/index.html), que consume la API publicada por HTTPS.
 * El host y el token de ingesta se configuran desde la propia pantalla.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var assetLoader: WebViewAssetLoader

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Publica assets/ bajo el dominio reservado appassets.androidplatform.net,
        // que Android resuelve localmente (no sale a la red).
        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        val fondo = Color.parseColor("#FCFAED")

        WebView.setWebContentsDebuggingEnabled(true)

        web = WebView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            settings.javaScriptEnabled = true
            // domStorage habilita localStorage, donde la pantalla guarda la URL
            // del backend y el token de ingesta introducidos por el operador.
            settings.domStorageEnabled = true
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            setBackgroundColor(fondo)

            webChromeClient = object : WebChromeClient() {
                override fun onConsoleMessage(consoleMessage: ConsoleMessage): Boolean {
                    Log.e("HD_CONSOLE", consoleMessage.message() + " -- línea " + consoleMessage.lineNumber() + " de " + consoleMessage.sourceId())
                    return true
                }
            }

            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(
                    view: WebView, request: WebResourceRequest
                ): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)

                override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                    super.onReceivedError(view, request, error)
                    Log.e("HD_NET_ERROR", "URL: " + (request?.url) + " -- Error: " + (error?.description))
                }
            }
        }

        setContentView(web)
        // Se sirve desde https://appassets.androidplatform.net y NO desde
        // file://: así la pantalla tiene un origen concreto que el backend puede
        // autorizar por CORS (un origen file:// viaja como `null`, que sería
        // indistinguible de cualquier HTML local y obligaría a abrir la lista).
        web.loadUrl("https://appassets.androidplatform.net/assets/public/index.html")
    }

    override fun onBackPressed() {
        if (web.canGoBack()) {
            web.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
