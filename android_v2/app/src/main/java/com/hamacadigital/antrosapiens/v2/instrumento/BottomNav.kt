package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

enum class NivelInstrumento(val ruta: String, val etiqueta: String) {
    EXPLORAR("explorar", "Explorar"),
    OBSERVAR("observar", "Observar"),
    TRIANGULAR("triangular", "Triangular"),
    FIJAR("fijar", "Fijar"),
}

/** Réplica de la <nav> fija de los 4 mockups (mismos 4 niveles, mismo estado activo). */
@Composable
fun BarraNiveles(actual: NivelInstrumento, onSeleccionar: (NivelInstrumento) -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
            .background(Mineral.Crema)
            .border(width = 1.dp, color = Mineral.NegroBorde)
            .padding(horizontal = 8.dp),
        horizontalArrangement = Arrangement.SpaceAround,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        NivelInstrumento.entries.forEach { nivel ->
            val activo = nivel == actual
            Row(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .clickable { onSeleccionar(nivel) }
                    .padding(vertical = 12.dp),
                horizontalArrangement = Arrangement.Center,
            ) {
                Text(
                    text = nivel.etiqueta.uppercase(),
                    style = TechLabelRegular,
                    fontWeight = if (activo) FontWeight.Bold else FontWeight.Normal,
                    color = if (activo) Mineral.Verde else Mineral.NegroSuave,
                )
            }
        }
    }
}
