package com.hamacadigital.antrosapiens.v2

import android.os.Bundle
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        setContentView(webView)

        webView.settings.javaScriptEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true
        webView.settings.cacheMode = WebSettings.LOAD_NO_CACHE

        // Sirve los assets bajo https://appassets.androidplatform.net (origen
        // real y estable) en vez de file:// (origen `null`). El backend de
        // Motor A (hd_scraper/api/app.py) ya autoriza por CORS exactamente
        // este origen — file:// nunca estuvo en su lista blanca porque un
        // origen `null` es indistinguible de cualquier HTML local ajeno.
        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                return assetLoader.shouldInterceptRequest(request.url)
            }
        }

        // Observabilidad (Fase 5, inspección del contrato de /verificados,
        // 2026-09-16): sin WebChromeClient, `console.log` desde el JS de
        // index.html no llega de forma garantizada a Logcat. Esto SOLO
        // reenvía los mensajes de consola ya existentes (o los que se
        // agreguen) al log — no cambia render, filtros ni comportamiento
        // visual. Ver `console.log` junto a los fetch de /verificados y
        // /mobile/scrape en index.html: permite observar con
        // `adb logcat -s AntroLabsHD-WebView` el JSON real que llegó al
        // dispositivo antes de pintarse.
        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(message: ConsoleMessage): Boolean {
                Log.d("AntroLabsHD-WebView",
                    "${message.message()} (${message.sourceId()}:${message.lineNumber()})")
                return true
            }
        }

        webView.loadUrl("https://appassets.androidplatform.net/assets/public/index.html")
    }
}
