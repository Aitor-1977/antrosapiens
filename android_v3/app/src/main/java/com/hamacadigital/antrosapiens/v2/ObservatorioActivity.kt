package com.hamacadigital.antrosapiens.v2

import android.content.Intent
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader

// Segunda función de AntroLabsHD, independiente del radar comercial de
// MainActivity: el Observatorio Antropológico del Ecosistema. Ventana
// separada a propósito (Activity propia, no una pestaña más del WebView de
// MainActivity) — mismo patrón de MainActivity.kt (WebViewAssetLoader sobre
// https://appassets.androidplatform.net, nunca file://), sirviendo su propio
// HTML (observatorio.html) contra los endpoints /observatorio/* del mismo
// backend de Motor A. No comparte estado ni WebView con MainActivity.
class ObservatorioActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        setContentView(webView)

        webView.settings.javaScriptEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true
        webView.settings.cacheMode = WebSettings.LOAD_NO_CACHE

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

        webView.loadUrl("https://appassets.androidplatform.net/assets/public/observatorio.html")
    }
}
