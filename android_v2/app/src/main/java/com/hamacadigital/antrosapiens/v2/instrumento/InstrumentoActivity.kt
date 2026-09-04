package com.hamacadigital.antrosapiens.v2.instrumento

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

/** Navega entre los 4 niveles sin acumular back stack (comportamiento típico de tabs). */
private fun NavHostController.irANivel(nivel: NivelInstrumento) {
    navigate(nivel.ruta) {
        popUpTo(graph.startDestinationId) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}

/**
 * Instrumento Pericial (V4, paleta Mineral) — cliente nativo Compose de los 4
 * niveles (Explorar / Observar / Triangular / Fijar). Independiente de
 * MainActivity: no reemplaza ni modifica el WebView del Radar en producción.
 * Contenido de ejemplo, igual al de los 4 HTML fuente; sin conexión a datos
 * reales todavía (ver hd_scraper doctrine: cualquier interpretación de
 * evidencia real que se agregue aquí debe respetar la Frontera de
 * Interpretación de CLAUDE.md).
 */
class InstrumentoActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AntrolabsHDTheme {
                val navController = rememberNavController()
                NavHost(navController = navController, startDestination = NivelInstrumento.EXPLORAR.ruta) {
                    composable(NivelInstrumento.EXPLORAR.ruta) {
                        ExplorarScreen(onSeleccionarNivel = { nivel -> navController.irANivel(nivel) })
                    }
                    composable(NivelInstrumento.OBSERVAR.ruta) {
                        ObservarScreen(onSeleccionarNivel = { nivel -> navController.irANivel(nivel) })
                    }
                    composable(NivelInstrumento.TRIANGULAR.ruta) {
                        TriangularScreen(onSeleccionarNivel = { nivel -> navController.irANivel(nivel) })
                    }
                    composable(NivelInstrumento.FIJAR.ruta) {
                        FijarScreen(onSeleccionarNivel = { nivel -> navController.irANivel(nivel) })
                    }
                }
            }
        }
    }
}
