import psycopg2, os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no está configurada.")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

principios = [
    ("P01", "REALIDAD SOCIAL", "Epistemología", "La realidad social es situada, histórica, relacional y dinámica.", "¿Estamos estudiando el sistema real o una representación simplificada?", True),
    ("P02", "UNIDAD DE ANÁLISIS", "Unidad de Análisis", "No estudiamos individuos aislados. Estudiamos relaciones entre personas, organizaciones, tecnologías e instituciones.", "¿Qué relación estamos observando?", True),
    ("P03", "PRÁCTICA", "Práctica", "La práctica tiene prioridad sobre el discurso. Lo que las personas hacen puede contradecir lo que dicen hacer.", "¿Tenemos evidencia de práctica o solamente declaraciones?", True),
    ("P04", "SIGNIFICADO", "Interpretación", "El significado emerge de la relación entre práctica, contexto, historia y posición social.", "¿Estamos interpretando el significado dentro de su contexto?", False),
    ("P05", "POSICIÓN DEL ENUNCIADOR", "Poder", "Toda evidencia posee una posición de enunciación. Importa quién habla, desde dónde y para quién.", "¿Quién produjo esta evidencia y qué posición ocupa?", True),
    ("P06", "EVIDENCIA", "Evidencia", "La evidencia debe ser trazable, contextualizada y diferenciada de la interpretación.", "¿Podemos demostrar de dónde salió esta afirmación?", True),
    ("P07", "SEÑALES ANTROPOLÓGICAS", "Señales", "Una señal adquiere valor cuando revela una tensión, relación, práctica o transformación cultural.", "¿Qué fenómeno cultural revela esta señal?", False),
    ("P08", "RECURRENCIA", "Interpretación", "Un evento aislado no constituye automáticamente un patrón. Buscamos recurrencias.", "¿Esto ocurre una vez o forma parte de un patrón?", True),
    ("P09", "ANOMALÍA", "Señales", "Las anomalías son potencialmente productoras de conocimiento. Lo que rompe el patrón merece investigación.", "¿Qué nos está mostrando aquello que no encaja?", False),
    ("P10", "CONTRADICCIÓN", "Fricción", "Las contradicciones entre discurso, práctica, institución y tecnología son objetos privileged.", "¿Dónde está la contradicción productiva?", False),
    ("P11", "FRICCIÓN", "Fricción", "Buscamos fricciones entre prácticas, expectativas, normas, tecnologías y relaciones.", "¿Cuál es la fricción que el sistema todavía no logra explicar?", True),
    ("P12", "DEUDA CULTURAL™", "Deuda Cultural™", "Los sistemas acumulan rituales, hábitos, atajos y soluciones informales que condicionan la innovación.", "¿Qué práctica preexistente compite con la nueva solución?", True),
    ("P13", "RITUALES", "Práctica", "Los rituales organizan comportamientos y producen continuidad, confianza, pertenencia y poder.", "¿Qué ritual mantiene funcionando este sistema?", False),
    ("P14", "SOLUCIONES INVISIBLES", "Deuda Cultural™", "Antes de cualquier innovación ya existen formas de resolver el problema: personas, WhatsApp, Excel.", "¿Qué solución ya existe aunque no aparezca en el producto?", False),
    ("P15", "INNOVACIÓN", "Innovación", "Toda innovación entra en un mundo previamente organizado. Altera relaciones y prácticas existentes.", "¿Qué sistema cultural está entrando en contacto con la innovación?", False),
    ("P16", "ADOPCIÓN", "Innovación", "Adoptar una innovación implica reorganizar relaciones, identidades, responsabilidades, poder y rutinas.", "¿Qué cambia socialmente cuando alguien adopta esto?", False),
    ("P17", "RESISTENCIA", "Poder", "La resistencia no debe interpretarse como irracionalidad. Puede proteger identidad, autonomía o continuidad.", "¿Qué está protegiendo la resistencia?", False),
    ("P18", "PODER", "Poder", "Toda innovación redistribuye poder, visibilidad, información, autonomía y capacidad de decisión.", "¿Quién gana, quién pierde y quién queda expuesto?", True),
    ("P19", "INSTITUCIONES", "Epistemología", "Las organizaciones son sistemas culturales con normas formales e informales, jerarquías y memoria.", "¿Qué reglas no escritas gobiernan realmente el sistema?", False),
    ("P20", "CATEGORÍAS", "Epistemología", "Categorías como usuario, cliente o empleado son construcciones institucionales, no realidades naturales.", "¿Quién creó esta categoría y qué deja fuera?", False),
    ("P21", "ONLIFE", "Onlife", "Lo digital y lo presencial forman parte de un mismo ecosistema sociotécnico.", "¿Qué ocurre entre el espacio digital y el mundo físico?", False),
    ("P22", "ETNOGRAFÍA DIGITAL", "Etnografía digital", "Internet no es solo fuente documental: es espacio de producción y transformación cultural.", "¿Qué prácticas culturales están ocurriendo en este entorno digital?", False),
    ("P23", "SCRAPING ANTROPOLÓGICO", "Etnografía digital", "Scraping es capturar señales situadas para reconstruir relaciones, tensiones y transformaciones.", "¿Qué conocimiento antropológico puede derivarse de este dato?", False),
    ("P24", "CORPUS", "Interpretación", "Ningún dato aislado explica un fenómeno. El conocimiento emerge de la configuración del corpus.", "¿Qué otras evidencias necesitamos para interpretar esta señal?", False),
    ("P25", "TRIANGULACIÓN", "Interpretación", "Una hipótesis gana fuerza cuando puede observarse desde diferentes posiciones, fuentes y situaciones.", "¿Qué evidencia independiente sostiene esta interpretación?", False),
    ("P26", "INTERPRETACIÓN", "Interpretación", "Evidencia, patrón, hipótesis y conclusión son niveles diferentes y nunca deben confundirse.", "¿Estamos presentando una interpretación como si fuera un hecho?", False),
    ("P27", "REFLEXIVIDAD", "Reflexividad", "El investigador forma parte de la producción del conocimiento. Sus supuestos deben cuestionarse.", "¿Qué estamos proyectando nosotros sobre el fenómeno?", True),
    ("P28", "DECOLONIALIDAD", "Decolonialidad", "No universalizamos categorías occidentales ni tratamos conocimientos locales como ruido.", "¿Qué epistemología estamos privilegiando?", False),
    ("P29", "NO EXTRACTIVISMO", "Decolonialidad", "Las personas no son depósitos de datos. El conocimiento debe producir capacidad.", "¿Qué devolvemos además de lo que extraemos?", False),
    ("P30", "SUJETOS DE CONOCIMIENTO", "Decolonialidad", "Las personas investigadas son productoras de conocimiento, no solo fuentes de información.", "¿Qué conocimiento posee el sujeto que nuestro marco no contempla?", False),
    ("P31", "COMPLEJIDAD", "Complejidad", "No reducimos fenómenos culturales complejos a una única variable causal.", "¿Qué estamos perdiendo al simplificar?", False),
    ("P32", "CONTEXTUALIDAD", "Temporalidad", "El mismo comportamiento adquiere significados diferentes según territorio, momento y situación.", "¿Qué contexto modifica el significado de esta práctica?", False),
    ("P33", "TEMPORALIDAD", "Temporalidad", "Los fenómenos culturales tienen historia, acumulación y trayectoria.", "¿Cómo llegó este sistema a ser lo que es hoy?", False),
    ("P34", "SITUACIONALIDAD", "Temporalidad", "Las prácticas cambian según circunstancias específicas.", "¿Qué cambia cuando cambia la situación?", True),
    ("P35", "AGENCIA", "Agencia", "Las personas negocian, adaptan, resisten y transforman estructuras.", "¿Dónde está la capacidad de agencia?", False),
    ("P36", "MATERIALIDAD", "Materialidad", "Objetos, espacios, interfaces y tecnologías participan en la producción de relaciones sociales.", "¿Qué papel juega lo material en este comportamiento?", False),
    ("P37", "SOCIOTECNIA", "Sociotecnia", "Tecnología y sociedad se co-producen.", "¿Qué transforma la tecnología y qué transforma la cultura en la tecnología?", False),
    ("P38", "INCERTIDUMBRE", "Acción", "La investigación antropológica busca reducir incertidumbre mediante evidencia.", "¿Qué todavía no sabemos?", False),
    ("P39", "HIPÓTESIS", "Acción", "Una hipótesis antropológica debe poder confrontarse con nueva evidencia.", "¿Qué evidencia podría demostrar que estamos equivocados?", False),
    ("P40", "ACCIÓN", "Acción", "El conocimiento antropológico debe aumentar la capacidad de comprender y decidir.", "¿Qué decisión puede mejorar gracias a este conocimiento?", False)
]

for p in principios:
    cursor.execute("""
        INSERT INTO principios_antropologicos (codigo, nombre, familia, descripcion, pregunta_control, es_nucleo_duro)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (codigo) DO UPDATE 
        SET nombre = EXCLUDED.nombre, descripcion = EXCLUDED.descripcion, pregunta_control = EXCLUDED.pregunta_control;
    """, p)

cursor.execute("""
    INSERT INTO organizaciones (id, nombre, sector, territorio, situacion_actual, estado_investigacion)
    VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Hamaca Digital', 'Laboratorio de Antropología de la Innovación', 'México', 'Despliegue de infraestructura epistemológica y Sprint Fundacional DolorMap', 'ACTIVO')
    ON CONFLICT (id) DO NOTHING;
""")

conn.commit()
cursor.close()
conn.close()
print("✅ Datos semillas inyectados con éxito en Neon.")
