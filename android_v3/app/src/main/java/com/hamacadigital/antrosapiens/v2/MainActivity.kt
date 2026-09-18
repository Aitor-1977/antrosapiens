package com.hamacadigital.antrosapiens.v2

import android.content.Intent
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader

class MainActivity : AppCompatActivity() {
    // Único puente hacia el Observatorio (segunda función, ventana aparte):
    // no toca ni lee el flujo INDAGAR/OBSERVAR/TRIANGULAR/FIJAR ni sus datos,
    // solo abre una Activity distinta. Excepción puntual autorizada por el
    // operador (Mario, 2026-09-18) al congelamiento de este archivo.
    private inner class PuenteObservatorio {
        @JavascriptInterface
        fun abrirObservatorio() {
            startActivity(Intent(this@MainActivity, ObservatorioActivity::class.java))
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        setContentView(webView)

        webView.settings.javaScriptEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true
        webView.settings.cacheMode = WebSettings.LOAD_NO_CACHE
        webView.addJavascriptInterface(PuenteObservatorio(), "PuenteObservatorio")

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

            // Un enlace a la fuente real de una evidencia (news.google.com
            // resuelto, o el medio directo) no es un asset de la app: se abre
            // en el navegador del sistema, no dentro de este WebView. Sin
            // esto, tocar "Ver fuente" reemplazaba la UI de la app por el
            // artículo externo, sin manera de volver (el WebView no tenía
            // pila de navegación propia configurada).
            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest
            ): Boolean {
                val url = request.url
                if (url.host == "appassets.androidplatform.net") return false
                startActivity(Intent(Intent.ACTION_VIEW, url))
                return true
            }
        }

        webView.loadUrl("https://appassets.androidplatform.net/assets/public/index.html")
    }
}
