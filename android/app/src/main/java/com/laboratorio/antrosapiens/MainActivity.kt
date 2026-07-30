package com.laboratorio.antrosapiens

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Lienzo principal de Antrosapiens.
 *
 * Pantalla base sin distracciones: fondo oscuro de la identidad del laboratorio
 * con el logotipo centrado. Construida en código (sin XML de layout) para
 * minimizar dependencias de recursos y garantizar una compilación estable.
 */
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val fondo = Color.parseColor("#111715")

        val raiz = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(fondo)
            setPadding(48, 48, 48, 48)
        }

        val logo = ImageView(this).apply {
            setImageResource(R.drawable.antrosapiens_logo)
            adjustViewBounds = true
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }

        val estado = TextView(this).apply {
            text = "Aplicación activa"
            textSize = 14f
            setTextColor(Color.parseColor("#2E7D64"))
            gravity = Gravity.CENTER
            setPadding(0, 32, 0, 0)
        }

        raiz.addView(logo)
        raiz.addView(estado)
        setContentView(raiz)
    }
}
