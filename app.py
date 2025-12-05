import streamlit as st
import pandas as pd
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Validación de Indicadores Ambientales",
    page_icon="🛣️",
    layout="wide"
)

# --- 2. ESTILOS VISUALES (TU PALETA DE COLORES) ---
st.markdown("""
    <style>
    /* Estilos para Radio Buttons */
    .stRadio > label {
        font-weight: bold; 
        color: #4A4F3E;
    }
    /* Estilos para Títulos de Sección */
    .big-font {
        font-size:20px !important; 
        color: #D95D4E; 
        font-weight: bold;
    }
    /* Estilos para los Expanders (Categorías) */
    div[data-testid="stExpander"] details summary p {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4A4F3E;
    }
    /* Estilo del Botón Principal */
    div.stButton > button:first-child {
        background-color: #D95D4E;
        color: white;
        font-size: 18px;
        border-radius: 10px;
        padding: 10px 24px;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #A3B946;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ESTADO DE LA APLICACIÓN ---
if 'etapa_evaluacion' not in st.session_state:
    st.session_state.etapa_evaluacion = False

# --- 4. LISTA MAESTRA DE INDICADORES (66 INDICADORES) ---
INDICADORES_MAESTROS = {
    "Calidad del Aire": [
        "Monitoreo de gases", 
        "Mediciones de calidad del aire", 
        "Cantidad de reportes de material particulado",
        "N° riegos realizados / N° riegos programados", 
        "N° mallas cortaviento implementadas / N° mallas cortaviento programadas",
        "N° inspecciones realizadas en acopio de materiales / N° inspecciones programadas", 
        "N° de lavados de llantas realizados / N° lavados de llantas programados"
    ],
    "Calidad del Agua": [
        "Mediciones de calidad del agua", 
        "N° de tomas de agua ilegales identificadas", 
        "N° de conexiones ilegales a cuerpos de agua",
        "Cantidad de sistemas de drenaje en sitio", 
        "Cantidad de obras para manejo de aguas en sitio", 
        "Reportes de mantenimiento de obras de drenaje",
        "Plan de manejo de aguas residuales", 
        "N° de inspecciones de manejo de aguas residuales / N° inspecciones programadas"
    ],
    "Gestión de Suelos y Erosión": [
        "Construcción de obras de control de erosión (Mínimo una trampa por escombrera)", 
        "Reporte de estabilidad de taludes (escombreras)",
        "Muestreos de suelo en plantel (cierre técnico)", 
        "Cantidad de obras en sitio (Cuencos temporales)",
        "Cantidad de reportes de sedimentos en áreas de trabajo y cauces receptores", 
        "Registros de protección de taludes"
    ],
    "Biodiversidad y Vegetación": [
        "Registro fotográfico de la reforestación (cierre técnico)", 
        "Cantidad de árboles sembrados y especies (cierre técnico)",
        "Zonas recreativas con recuperación de vegetación (cierre técnico)", 
        "N° de permisos de tala, poda y reubicación",
        "Registro fotográfico de la reubicación de fauna", 
        "Registros de mantenimiento de cobertura vegetal en taludes",
        "Registros de programas de reforestación", 
        "Registros de rescate y reubicación de fauna", 
        "Registros de permisos de aprovechamiento forestal"
    ],
    "Gestión de Residuos": [
        "Planos as built y certificado de cierre técnico (escombreras)", 
        "N° de obras temporales (planteles) con cierre técnico",
        "Autorización de cierre técnico del plantel (regente)", 
        "Indicadores de Uso y Cierre Técnico de Escombreras",
        "Indicadores de Instalación y Cierre de Obras Temporales", 
        "Plan de Manejo de Residuos (PMR)",
        "Plan de gestión de residuos peligrosos", 
        "N° de inspecciones de manejo de residuos / N° inspecciones programadas"
    ],
    "Gestión de Sustancias y Derrames": [
        "N° de incidentes por derrames de hidrocarburos", 
        "N° de eventos de capacitación en manejo de hidrocarburos",
        "Registros de mantenimiento de filtros, piletas y atención de derrames", 
        "Plan de manejo de sustancias peligrosas",
        "N° de reportes de derrames atendidos / N° total de derrames", 
        "N° de inspecciones de manejo de sustancias peligrosas / N° inspecciones programadas"
    ],
    "Patrimonio Cultural": [
        "N° de visitas del profesional en arqueología (si es necesario)", 
        "N° de evidencia arqueológica", 
        "Indicadores de Arqueología"
    ],
    "Gestión Socioeconómica y SSO": [
        "N° de quejas de terceros", 
        "N° de multas o sanciones a transportistas", 
        "Monitoreo de ruido",
        "Nº de señales viales colocadas y Nº de pasos peatonales", 
        "Registros de colocación de vallas de protección",
        "Registros de capacitación al personal de la obra", 
        "Cantidad de reportes de quejas por ruido y vibraciones",
        "Registro de permiso del Ministerio de Salud para campamentos", 
        "N° de inspecciones de manejo de ruido / N° inspecciones programadas",
        "N° de inspecciones socioambientales / N° programadas", 
        "N° de inspecciones de salud y seguridad / N° programadas",
        "N° de reportes de accidentes / N° total de horas trabajadas"
    ],
    "Gestión de Proyecto y Cumplimiento": [
        "Registro fotográfico de limpieza de accesos", 
        "N° de vehículos con revisión técnica vehicular (RTV) al día",
        "Reporte de regencia ambiental (cierre técnico)", 
        "Cierre técnico al final del proyecto: Notas de los profesionales...",
        "Planos de diseño del proyecto", 
        "Registros de revisión de maquinaria y equipo", 
        "Reportes de inspección de fugas en maquinaria y equipo"
    ]
}

# --- 5. INTERFAZ DE USUARIO: TÍTULO ---
st.title("🛣️ Validación de Indicadores Ambientales para Proyectos Viales")
st.markdown("""
**Instrucciones:**
1. Complete sus datos profesionales.
2. Seleccione y proponga indicadores clave (Etapa de Selección).
3. Habilite la evaluación para calificar los indicadores elegidos (Etapa de Evaluación).
""")
st.divider()

# --- 6. SECCIÓN I: DATOS DEL PROFESIONAL ---
st.subheader("I. Datos del Profesional")
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre Completo (Opcional)")
    profesion = st.text_input("Profesión / Especialidad", placeholder="Ej. Ingeniero Civil, Biólogo...")
    nivel_acad = st.selectbox("Nivel Académico", ["Bachillerato", "Licenciatura", "Maestría", "Doctorado"])
with col2:
    provincia = st.selectbox("Provincia de Residencia/Trabajo", ["San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón", "Fuera de Costa Rica"])
    experiencia = st.selectbox("Años de Experiencia en Infraestructura", 
                               ["No tengo experiencia en infraestructura", "Menos de 5 años", "5 - 10 años", "Más de 10 años"])

st.divider()

# --- 7. SECCIÓN II: SELECCIÓN DE INDICADORES ---
st.subheader("II. Selección de Indicadores")
st.info("Seleccione al menos 2 indicadores por categoría. Si falta alguno, agréguelo en los espacios opcionales.")

# Diccionarios para guardar temporalmente las selecciones
dict_seleccionados = {}
dict_nuevos = {}

# Bucle para crear los controles de cada categoría
for categoria, lista_indicadores in INDICADORES_MAESTROS.items():
    with st.expander(f"📂 Categoría: {categoria}", expanded=False):
        
        # Multiselect de indicadores existentes
        sel = st.multiselect(
            f"Seleccione indicadores clave para {categoria}:",
            options=lista_indicadores,
            key=f"sel_{categoria}"
        )
        dict_seleccionados[categoria] = sel
        
        # Advertencia visual si seleccionan menos de 2
        if len(sel) > 0 and len(sel) < 2:
            st.warning("⚠️ Se recomienda seleccionar un mínimo de 2 indicadores.")

        # Campos para nuevos indicadores
        col_new1, col_new2 = st.columns(2)
        n1 = col_new1.text_input(f"Indicador Adicional 1", key=f"new1_{categoria}", placeholder="Opcional")
        n2 = col_new2.text_input(f"Indicador Adicional 2", key=f"new2_{categoria}", placeholder="Opcional")
        
        # Guardar nuevos
        nuevos_lista = []
        if n1: nuevos_lista.append(f"(NUEVO) {n1}")
        if n2: nuevos_lista.append(f"(NUEVO) {n2}")
        dict_nuevos[categoria] = nuevos_lista

# --- 8. BOTÓN DE TRANSICIÓN ---
st.markdown("---")
col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
with col_b2:
    if st.button("⬇️ Finalizar Selección y Habilitar Evaluación Likert ⬇️", use_container_width=True):
        st.session_state.etapa_evaluacion = True
        st.rerun()

# --- 9. SECCIÓN III: EVALUACIÓN LIKERT ---
if st.session_state.etapa_evaluacion:
    st.markdown("---")
    st.subheader("III. Evaluación de Indicadores Seleccionados")
    st.warning("⚠️ IMPORTANTE: Para enviar la encuesta, es obligatorio marcar una opción (DA, N, ED) para CADA UNO de los 4 criterios en TODOS los indicadores listados abajo.")
    
    with st.form("form_evaluacion_final"):
        
        criterios = ["Claridad en Redacción", "Pertinencia Ambiental", "Factibilidad de Medición", "Relevancia Control"]
        opciones_likert = ["De Acuerdo (DA)", "Neutro (N)", "En Desacuerdo (ED)"]
        hay_items_para_evaluar = False
        
        # Mostrar indicadores seleccionados para evaluar
        for categoria in INDICADORES_MAESTROS.keys():
            items_totales = dict_seleccionados.get(categoria, []) + dict_nuevos.get(categoria, [])
            
            if items_totales:
                hay_items_para_evaluar = True
                st.markdown(f"#### 🔹 {categoria}")
                for ind in items_totales:
                    st.markdown(f"**Indicador: {ind}**")
                    cols = st.columns(4)
                    for i, crit in enumerate(criterios):
                        cols[i].radio(
                            crit, 
                            opciones_likert, 
                            key=f"EVAL|{categoria}|{ind}|{crit}", 
                            horizontal=True, 
                            index=None
                        )
                st.markdown("---")

        # Botón de envío final
        submitted = st.form_submit_button("🚀 Enviar Encuesta Final")
        
        if submitted:
            # A. Validaciones básicas
            if not nombre or not profesion:
                st.error("⚠️ Por favor suba al inicio y complete su Nombre y Profesión.")
            elif not hay_items_para_evaluar:
                st.error("⚠️ No ha seleccionado ningún indicador para evaluar.")
            else:
                # B. Validación de Completitud (Buscar nulos)
                preguntas_faltantes = 0
                for categoria in INDICADORES_MAESTROS.keys():
                    items = dict_seleccionados.get(categoria, []) + dict_nuevos.get(categoria, [])
                    for ind in items:
                        for crit in criterios:
                            key_check = f"EVAL|{categoria}|{ind}|{crit}"
                            if st.session_state.get(key_check) is None:
                                preguntas_faltantes += 1
                
                if preguntas_faltantes > 0:
                    st.error(f"❌ ERROR: No se puede enviar. Faltan {preguntas_faltantes} respuestas por marcar. Revise que todas las filas tengan opción seleccionada.")
                else:
                    # C. PROCESO DE GUARDADO OPTIMIZADO (LOTE)
                    try:
                        # 1. Autenticación con Google
                        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                        creds_dict = dict(st.secrets["gcp_service_account"])
                        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                        client = gspread.authorize(creds)
                        
                        # 2. Abrir hoja de cálculo
                        sheet = client.open("Base_Datos_TFG").sheet1
                        
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 3. Recolectar TODAS las filas en una lista (El "Autobús")
                        todas_las_filas = []
                        
                        for key, val in st.session_state.items():
                            if key.startswith("EVAL|") and val is not None:
                                parts = key.split("|")
                                if len(parts) == 4:
                                    _, cat, ind, crit = parts
                                    
                                    # Construir fila individual
                                    fila = [
                                        timestamp, nombre, profesion, nivel_acad, provincia, 
                                        experiencia, cat, ind, 
                                        "Nuevo" if "(NUEVO)" in ind else "Predefinido", 
                                        crit, val
                                    ]
                                    todas_las_filas.append(fila)
                        
                        # 4. Enviar el lote completo (UNA sola petición a la API)
                        if todas_las_filas:
                            sheet.append_rows(todas_las_filas)
                            
                            st.balloons()
                            st.success(f"¡Muchas gracias, {nombre}! Su encuesta ha sido enviada y guardada en la nube exitosamente.")
                            st.info("Ya puede cerrar esta pestaña.")
                        
                    except Exception as e:
                        st.error("⚠️ Ocurrió un error al conectar con la base de datos.")
                        st.code(f"Error: {e}")