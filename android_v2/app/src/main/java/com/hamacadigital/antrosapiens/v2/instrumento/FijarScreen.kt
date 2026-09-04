package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/** Réplica de nivel_3_fijar_antrolabshd_v4_mineral.html (NIVEL 3: Inspector de Evidencias). */
@Composable
fun FijarScreen(onSeleccionarNivel: (NivelInstrumento) -> Unit, onSellarPeritaje: () -> Unit = {}) {
    InstrumentoScaffold(
        nivelActual = NivelInstrumento.FIJAR,
        etiquetaNivel = "NIVEL 3",
        onSeleccionarNivel = onSeleccionarNivel,
        tituloHeader = {
            Text(text = "Inspector de Evidencias", style = VoiceHeading, color = Mineral.Verde)
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
                    .border(1.dp, Mineral.Verde, RoundedCornerShape(12.dp))
                    .padding(20.dp),
            ) {
                Text(
                    text = "Lectura Pericial",
                    style = VoiceHeading,
                    color = Mineral.Negro,
                    modifier = Modifier.padding(bottom = 8.dp),
                )
                Text(
                    text = "Tras la triangulación de los registros etnográficos, se dictamina " +
                        "que la adopción presenta fallos sociotécnicos estructurales.",
                    style = VoiceQuoteSmall,
                    color = Mineral.Negro.copy(alpha = 0.9f),
                    modifier = Modifier.padding(bottom = 16.dp),
                )
                Text(
                    text = "SELLAR PERITAJE",
                    style = TechLabel,
                    color = Color.White,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Mineral.Verde, RoundedCornerShape(8.dp))
                        .clickable { onSellarPeritaje() }
                        .padding(vertical = 12.dp),
                )
            }
        }
    }
}
