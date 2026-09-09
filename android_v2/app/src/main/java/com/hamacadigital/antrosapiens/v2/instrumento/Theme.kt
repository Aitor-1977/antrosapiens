package com.hamacadigital.antrosapiens.v2.instrumento

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * Paleta Mineral (AntrolabsHD V4). Fuentes: se usan las familias genéricas de
 * Compose (Serif/Monospace/SansSerif) como aproximación de Playfair Display /
 * IBM Plex Mono / Inter, para no depender de certificados de Google Fonts ni
 * de binarios de fuente embebidos. Si se requiere match tipográfico exacto,
 * es una ampliación aparte (bundlear los .ttf en res/font/).
 */
object Mineral {
    val Crema = Color(0xFFE8E4DC)
    val Verde = Color(0xFF5A7A00)
    val Negro = Color(0xFF111111)
    val Rojo = Color(0xFFB00020)
    val Azul = Color(0xFF1F5C8C)
    val Blanco = Color(0xFFFFFFFF)

    val NegroSuave = Negro.copy(alpha = 0.6f)
    val NegroBorde = Negro.copy(alpha = 0.1f)
}

private val EsquemaMineral = lightColorScheme(
    background = Mineral.Crema,
    surface = Mineral.Blanco,
    primary = Mineral.Verde,
    onPrimary = Mineral.Blanco,
    error = Mineral.Rojo,
    onError = Mineral.Blanco,
    secondary = Mineral.Azul,
    onBackground = Mineral.Negro,
    onSurface = Mineral.Negro,
)

// font-tech: IBM Plex Mono -> Monospace
val TechLabel = TextStyle(
    fontFamily = FontFamily.Monospace,
    fontSize = 11.sp,
    fontWeight = FontWeight.Bold,
    letterSpacing = 0.6.sp,
)
val TechLabelRegular = TextStyle(
    fontFamily = FontFamily.Monospace,
    fontSize = 12.sp,
)

// font-serif-voice: Playfair Display -> Serif
val VoiceTitle = TextStyle(
    fontFamily = FontFamily.Serif,
    fontSize = 28.sp,
    fontWeight = FontWeight.SemiBold,
    lineHeight = 34.sp,
)
val VoiceHeading = TextStyle(
    fontFamily = FontFamily.Serif,
    fontSize = 20.sp,
    fontWeight = FontWeight.SemiBold,
)
val VoiceQuote = TextStyle(
    fontFamily = FontFamily.Serif,
    fontSize = 16.sp,
    fontStyle = FontStyle.Italic,
)
val VoiceQuoteSmall = TextStyle(
    fontFamily = FontFamily.Serif,
    fontSize = 15.sp,
    fontStyle = FontStyle.Italic,
)
val VoiceBody = TextStyle(
    fontFamily = FontFamily.Serif,
    fontSize = 14.sp,
)

// Inter -> SansSerif (cuerpo de interfaz)
val BodyText = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 14.sp,
    lineHeight = 20.sp,
)

@Composable
fun AntrolabsHDTheme(content: @Composable () -> Unit) {
    // Diseño mineral es un único tema claro: no distingue modo oscuro.
    MaterialTheme(
        colorScheme = EsquemaMineral,
        content = content,
    )
}
