package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Réplica de nivel_0_explorar_antrolabshd_v4_mineral.html (NIVEL 0: EXPLORAR). */
@Composable
fun ExplorarScreen(onSeleccionarNivel: (NivelInstrumento) -> Unit) {
    InstrumentoScaffold(
        nivelActual = NivelInstrumento.EXPLORAR,
        etiquetaNivel = "NIVEL 0: EXPLORAR",
        onSeleccionarNivel = onSeleccionarNivel,
        tituloHeader = {
            Row {
                Icon(
                    imageVector = Icons.Default.Search,
                    contentDescription = null,
                    tint = Mineral.Verde,
                    modifier = Modifier.padding(end = 6.dp),
                )
                Text(text = "AS-2024-X", style = TechLabel, color = Mineral.Verde)
            }
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState())
                .padding(top = 24.dp),
        ) {
            Text(
                text = "¿Cómo están mutando los rituales de ahorro en la generación Z?",
                style = VoiceTitle,
                color = Mineral.Negro,
                modifier = Modifier.padding(bottom = 16.dp),
            )
            Text(
                text = "Observaciones iniciales sugieren una transición del acaparamiento " +
                    "defensivo hacia un modelo de \"liquidez fluida\", donde el ahorro no se " +
                    "concibe como estasis, sino como potencial.",
                style = BodyText,
                color = Mineral.Negro.copy(alpha = 0.8f),
                modifier = Modifier.padding(bottom = 24.dp),
            )
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.White.copy(alpha = 0.8f), RoundedCornerShape(12.dp))
                    .border(1.dp, Mineral.NegroBorde, RoundedCornerShape(12.dp))
                    .padding(16.dp),
            ) {
                Text(
                    text = "SEÑAL PRIMARIA VERIFICADA",
                    style = TechLabel.copy(fontSize = 10.sp),
                    color = Mineral.Verde,
                )
                Text(
                    text = "\"El dinero quieto es dinero muerto, pero el dinero en movimiento " +
                        "constante genera ansiedad.\"",
                    style = VoiceQuoteSmall,
                    color = Mineral.Negro,
                    modifier = Modifier.padding(top = 8.dp, bottom = 12.dp),
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(text = "Fuente: Entrevista S-04", style = TechLabelRegular, color = Mineral.NegroSuave)
                    Text(text = "VERIFICADO", style = TechLabelRegular, color = Mineral.NegroSuave)
                }
            }
        }
    }
}
