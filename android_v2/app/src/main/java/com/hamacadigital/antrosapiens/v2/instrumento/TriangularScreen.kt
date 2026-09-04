package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Réplica de nivel_2_triangular_antrolabshd_v4_mineral.html (NIVEL 2: Mesa de Relaciones). */
@Composable
fun TriangularScreen(onSeleccionarNivel: (NivelInstrumento) -> Unit) {
    InstrumentoScaffold(
        nivelActual = NivelInstrumento.TRIANGULAR,
        etiquetaNivel = "NIVEL 2",
        onSeleccionarNivel = onSeleccionarNivel,
        tituloHeader = {
            Text(text = "Mesa de Relaciones", style = VoiceHeading, color = Mineral.Verde)
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
                    .border(1.dp, Mineral.Rojo.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                    .padding(16.dp),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "[!] CONTRADICE",
                        style = TechLabel.copy(fontSize = 10.sp),
                        color = Color.White,
                        modifier = Modifier
                            .background(Mineral.Rojo, RoundedCornerShape(4.dp))
                            .padding(horizontal = 8.dp, vertical = 2.dp),
                    )
                    Text(
                        text = "TGM-902 vs REP-044",
                        style = TechLabelRegular,
                        color = Mineral.NegroSuave,
                        modifier = Modifier.padding(start = 8.dp),
                    )
                }
                Text(
                    text = "Los rituales de desconexión matutina contradicen directamente el " +
                        "reporte oficial de engagement digital.",
                    style = VoiceBody,
                    color = Mineral.Negro,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
    }
}
