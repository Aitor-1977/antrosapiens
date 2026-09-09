package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Estructura común a los 4 niveles: header sticky (título + etiqueta de
 * nivel) + contenido + barra de navegación inferior. Réplica del <header>/
 * <nav> compartidos por los 4 HTML fuente.
 */
@Composable
fun InstrumentoScaffold(
    nivelActual: NivelInstrumento,
    tituloHeader: @Composable () -> Unit,
    etiquetaNivel: String,
    onSeleccionarNivel: (NivelInstrumento) -> Unit,
    content: @Composable (PaddingValues) -> Unit,
) {
    Scaffold(
        containerColor = Mineral.Crema,
        topBar = {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(64.dp)
                    .background(Mineral.Crema)
                    .border(width = 1.dp, color = Mineral.NegroBorde)
                    .padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                tituloHeader()
                Text(text = etiquetaNivel, style = TechLabelRegular, color = Mineral.NegroSuave)
            }
        },
        bottomBar = { BarraNiveles(actual = nivelActual, onSeleccionar = onSeleccionarNivel) },
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize()) {
            content(padding)
        }
    }
}
