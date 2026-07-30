package com.laboratorio.antrosapiens

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Lienzo principal de Antrosapiens.
 *
 * Pantalla base sin distracciones: construye la vista en código (sin XML de
 * layout) para minimizar dependencias de recursos y garantizar una compilación
 * estable. Solo confirma que la aplicación está activa.
 */
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val raiz = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.parseColor("#F8F9FA"))
            setPadding(48, 48, 48, 48)
        }

        val titulo = TextView(this).apply {
            text = "Antrosapiens"
            textSize = 32f
            setTextColor(Color.parseColor("#4F46E5"))
            gravity = Gravity.CENTER
        }

        val estado = TextView(this).apply {
            text = "Aplicación activa"
            textSize = 16f
            setTextColor(Color.parseColor("#1A1A1A"))
            gravity = Gravity.CENTER
            setPadding(0, 24, 0, 0)
        }

        raiz.addView(titulo)
        raiz.addView(estado)
        setContentView(raiz)
    }
}
