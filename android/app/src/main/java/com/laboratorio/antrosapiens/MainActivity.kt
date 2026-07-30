package com.laboratorio.antrosapiens

import android.annotation.SuppressLint
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

/**
 * Antrosapiens — puerta de entrada al laboratorio.
 *
 * La app carga RadarHD (el radar de prospectos, ya en producción) dentro de un
 * WebView, de modo que abrir Antrosapiens = entrar directo al trabajo real de
 * prospección. Mientras carga se muestra una portada con el logotipo.
 *
 * Construida en código (sin XML de layout) para minimizar dependencias de
 * recursos y garantizar una compilación estable.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView

    // Destino: RadarHD en producción. Cambiar aquí si la URL cambia.
    private val destino = "https://lemures-66.vercel.app/lab/dashboard"

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val fondo = Color.parseColor("#111715")
        val contenedor = FrameLayout(this).apply { setBackgroundColor(fondo) }

        // --- WebView con RadarHD ---
        web = WebView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            setBackgroundColor(fondo)
        }

        // --- Portada de carga (logo sobre fondo oscuro) ---
        val portada = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(fondo)
            setPadding(48, 48, 48, 48)
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }
        val logo = ImageView(this).apply {
            setImageResource(R.drawable.antrosapiens_logo)
            adjustViewBounds = true
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }
        val cargando = TextView(this).apply {
            text = "Cargando RadarHD…"
            textSize = 14f
            setTextColor(Color.parseColor("#2E7D64"))
            gravity = Gravity.CENTER
            setPadding(0, 32, 0, 0)
        }
        portada.addView(logo)
        portada.addView(cargando)

        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                // Oculta la portada al terminar de cargar el radar.
                portada.visibility = View.GONE
            }
        }

        contenedor.addView(web)
        contenedor.addView(portada)
        setContentView(contenedor)

        // Botón atrás: navega el historial del WebView antes de cerrar la app.
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (web.canGoBack()) web.goBack() else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        web.loadUrl(destino)
    }
}
