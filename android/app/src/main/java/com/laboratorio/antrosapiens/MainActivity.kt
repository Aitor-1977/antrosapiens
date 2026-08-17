package com.laboratorio.antrosapiens

import android.annotation.SuppressLint
import android.graphics.Color
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

/**
 * AntroSapiens V4 — Laboratorio de Pensamiento Antropológico
 *
 * La app carga la interfaz web local desde assets/public/index.html
 * y permite que esa interfaz se comunique con el backend Python
 * que corre en Termux en http://127.0.0.1:8000
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val fondo = Color.parseColor("#FCFAED")

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
            setBackgroundColor(fondo)
            webViewClient = WebViewClient()
        }

        setContentView(web)
        web.loadUrl("file:///android_asset/public/index.html")
    }

    override fun onBackPressed() {
        if (web.canGoBack()) {
            web.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
