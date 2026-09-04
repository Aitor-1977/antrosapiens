package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Réplica de nivel_1_observar_antrolabshd_v4_mineral.html (NIVEL 1: Mesa de Evidencias). */
@Composable
fun ObservarScreen(onSeleccionarNivel: (NivelInstrumento) -> Unit) {
    InstrumentoScaffold(
        nivelActual = NivelInstrumento.OBSERVAR,
        etiquetaNivel = "NIVEL 1",
        onSeleccionarNivel = onSeleccionarNivel,
        tituloHeader = {
            Text(text = "Mesa de Evidencias", style = VoiceHeading, color = Mineral.Verde)
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState())
                .padding(top = 24.dp),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.White, RoundedCornerShape(12.dp))
                    .border(1.dp, Mineral.Verde.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                    .padding(20.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(text = "EV-2024-04-12A", style = TechLabel, color = Mineral.Verde)
                    Text(
                        text = "VERIFICADO",
                        style = TechLabel.copy(fontSize = 10.sp),
                        color = Mineral.Verde,
                        modifier = Modifier
                            .background(Mineral.Verde.copy(alpha = 0.1f), RoundedCornerShape(4.dp))
                            .padding(horizontal = 8.dp, vertical = 2.dp),
                    )
                }
                Text(
                    text = "\"El sistema nuevo nos obliga a registrar todo dos veces. Dicen que " +
                        "es para agilizar, pero en la práctica termino llevándome trabajo a casa...\"",
                    style = VoiceQuote,
                    color = Mineral.Negro,
                    modifier = Modifier.padding(top = 12.dp, bottom = 12.dp),
                )
                HorizontalDivider(color = Mineral.NegroBorde, thickness = 1.dp)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(text = "Actor: M. Roldán (Operaciones)", style = TechLabelRegular, color = Mineral.NegroSuave)
                    Text(text = "12 Abr 2024", style = TechLabelRegular, color = Mineral.NegroSuave)
                }
            }
        }
    }
}
