import streamlit as st
import os
import pandas as pd
from pathlib import Path
import logging
import html
import time
from typing import Any, cast, Dict, Union, Optional

# Set page config
st.set_page_config(layout='wide', page_title='Archivos - Anclora AI RAG', page_icon='📁')

# Add the app directory to Python path for imports
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
for path_option in (project_root, app_dir):
    if path_option and path_option not in sys.path:
        sys.path.insert(0, path_option)

# Importar colores de Anclora RAG
from common.anclora_colors import apply_anclora_theme, ANCLORA_RAG_COLORS, create_colored_alert
from common.constants import CHROMA_CLIENT, CHROMA_COLLECTIONS

# Aplicar tema de colores Anclora RAG
apply_anclora_theme()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Streamlit compatibility helpers
_st = cast(Any, st)

# Type-safe session state helpers
def get_session_state_value(key: str, default: Any = None) -> Any:
    """Safely get a value from session state."""
    try:
        return st.session_state.get(key, default)
    except AttributeError:
        return default

def set_session_state_value(key: str, value: Any) -> None:
    """Safely set a value in session state."""
    try:
        st.session_state[key] = value  # type: ignore
    except (AttributeError, TypeError):
        # Fallback: try using setattr if dict-style assignment fails
        try:
            setattr(st.session_state, key, value)
        except AttributeError:
            logger.warning(f"Could not set session state value for key: {key}")

def has_session_state_key(key: str) -> bool:
    """Check if a key exists in session state."""
    try:
        return key in st.session_state
    except (AttributeError, TypeError):
        return False

def markdown_html(markdown_text: str) -> None:
    """Render HTML content with HTML support when available."""
    markdown_fn = getattr(_st, 'markdown', None)
    if callable(markdown_fn):
        try:
            markdown_fn(markdown_text, unsafe_allow_html=True)
        except TypeError:
            markdown_fn(markdown_text)
    else:
        st.write(markdown_text)

def show_caption(message: str) -> None:
    caption_fn = getattr(_st, 'caption', None)
    if callable(caption_fn):
        caption_fn(message)
    else:
        markdown_html(f"<p class='st-caption'>{html.escape(message)}</p>")

def stop_app() -> None:
    stop_fn = getattr(_st, 'stop', None)
    if callable(stop_fn):
        stop_fn()
    else:
        raise RuntimeError('Streamlit.stop is not available in this version')

def show_checkbox(label: str, **kwargs: Any) -> bool:
    checkbox_fn = getattr(_st, 'checkbox', None)
    if callable(checkbox_fn):
        return bool(checkbox_fn(label, **kwargs))
    toggle_fn = getattr(_st, 'toggle', None)
    if callable(toggle_fn):
        return bool(toggle_fn(label, **kwargs))
    raise RuntimeError('Streamlit.checkbox is not available in this version')

def show_code(code_block: str, language: str = 'text') -> None:
    code_fn = getattr(_st, 'code', None)
    if callable(code_fn):
        code_fn(code_block, language=language)
    else:
        markdown_html(f"<pre><code>{html.escape(code_block)}</code></pre>")

def show_metric(label: str, value: Any) -> None:
    metric_fn = getattr(_st, 'metric', None)
    if callable(metric_fn):
        metric_fn(label=label, value=value)
    else:
        st.write(f"{label}: {value}")

def get_text_input(label: str, **kwargs: Any) -> str:
    text_input_fn = getattr(_st, 'text_input', None)
    if callable(text_input_fn):
        return str(text_input_fn(label, **kwargs))
    text_area_fn = getattr(_st, 'text_area', None)
    if callable(text_area_fn):
        return str(text_area_fn(label, **kwargs))
    raise RuntimeError('Streamlit.text_input is not available in this version')

# CSS personalizado con colores Anclora RAG
custom_style = f"""
    <style>
        /* ============================================
           GLOBAL STREAMLIT ELEMENT HIDING
           ============================================ */
        #MainMenu {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        footer {{visibility: hidden;}}
        #stDecoration {{display:none;}}
        .stApp > div[data-testid="stToolbar"] {{display: none;}}

        /* ============================================
           SIDEBAR STYLING
           ============================================ */
        div[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] .stMarkdown h3,
        section[data-testid="stSidebar"] h3,
        .sidebar h3 {{
            color: white !important;
        }}

        div[data-testid="stSidebar"] .stSelectbox label,
        div[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] label {{
            color: white !important;
            font-weight: 600 !important;
        }}

        .sidebar .stSelectbox > div > div {{
            background-color: rgba(255,255,255,0.1) !important;
            border: 2px solid #2EAFC4 !important;
            border-radius: 8px !important;
            color: white !important;
        }}

        /* ============================================
           FILE UPLOADER STYLING
           ============================================ */
        .stFileUploader label {{
            color: white !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
        }}

        .stFileUploader > div > div {{
            background-color: {ANCLORA_RAG_COLORS['neutral_medium']} !important;
            border: 2px solid white !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
        }}

        .stFileUploader button {{
            background-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']} !important;
            border-radius: 8px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
        }}

        .stFileUploader button:hover {{
            background-color: {ANCLORA_RAG_COLORS['primary_deep']} !important;
            border-color: {ANCLORA_RAG_COLORS['primary_deep']} !important;
        }}

        /* ============================================
           BUTTON STYLING
           ============================================ */
        .stButton > button {{
            background: linear-gradient(135deg, {ANCLORA_RAG_COLORS['success']} 0%, {ANCLORA_RAG_COLORS['primary_medium']} 100%) !important;
            border: 2px solid {ANCLORA_RAG_COLORS['success']} !important;
            border-radius: 12px !important;
            color: #1a4d47 !important;
            font-weight: 700 !important;
            padding: 0.6rem 1.5rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }}

        .stButton > button:hover {{
            background: {ANCLORA_RAG_COLORS['primary_deep']} !important;
            color: #0f3027 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.15) !important;
        }}

        /* ============================================
           DATAFRAME STYLING
           ============================================ */
        .stDataFrame {{
            border: 2px solid {ANCLORA_RAG_COLORS['primary_light']} !important;
            border-radius: 12px !important;
        }}

        /* ============================================
           FILES TITLE STYLING
           ============================================ */
        .files-title {{
            color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
        }}
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# Initialize language in session state
if not has_session_state_key('language'):
    set_session_state_value('language', 'es')

# Try to import ingest functions
INGEST_AVAILABLE = False
ingest_file = None
validate_uploaded_file = None
get_unique_sources_df = None
delete_file_from_vectordb = None
SUPPORTED_EXTENSIONS = []
CHROMA_SETTINGS = None  # ya no se usa para listar, pero se mantiene por compat

try:
    from common.ingest_file import ingest_file, validate_uploaded_file, get_unique_sources_df, delete_file_from_vectordb, SUPPORTED_EXTENSIONS
    from common.constants import CHROMA_CLIENT, CHROMA_COLLECTIONS
    INGEST_AVAILABLE = True
    st.success("✅ Módulos de ingesta cargados correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar módulos de ingesta: {e}")
    st.info("🔧 Verificando configuración del sistema...")

# Sidebar for language selection
with st.sidebar:
    st.header("🌐 Selección de Idioma")

    language_options = {
        'es': 'Español',
        'en': 'English'
    }

    current_language = get_session_state_value('language', 'es')
    selected_language = st.selectbox(
        "Selecciona idioma:",
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=0 if current_language == 'es' else 1,
        key="language_selector"
    )

    # Update session state if language changed
    current_language = get_session_state_value('language', 'es')
    if selected_language != current_language:
        set_session_state_value('language', selected_language)
        st.rerun()

# Main content
current_language = get_session_state_value('language', 'es')
if current_language == 'es':
    st.title("📁 Gestión de Archivos")
    show_caption("Sube y gestiona documentos para el sistema RAG")
    upload_label = "Subir archivo"
    add_button_text = "Añadir a la base de conocimiento"
    files_table_title = "Archivos en la base de datos"
    delete_button_text = "Eliminar archivo"
    processing_message = "Procesando archivo..."
    success_message = "Archivo agregado exitosamente"
    error_message = "Error al procesar archivo"
    no_files_message = "No hay archivos en la base de datos actualmente."
    upload_first_message = "Por favor, sube un archivo primero."
else:
    st.title("📁 File Management")
    show_caption("Upload and manage documents for the RAG system")
    upload_label = "Upload file"
    add_button_text = "Add to knowledge base"
    files_table_title = "Files in database"
    delete_button_text = "Delete file"
    processing_message = "Processing file..."
    success_message = "File added successfully"
    error_message = "Error processing file"
    no_files_message = "No files in database currently."
    upload_first_message = "Please upload a file first."

# Check if ingest functionality is available
if not INGEST_AVAILABLE:
    if current_language == 'es':
        st.error("⚠️ Los módulos de ingesta no están disponibles. Verifica la configuración del sistema.")
    else:
        st.error("⚠️ Ingest modules are not available. Please check system configuration.")
    stop_app()

# Show supported file types
if INGEST_AVAILABLE:
    supported_types = [ext.replace('.', '') for ext in SUPPORTED_EXTENSIONS]
    if current_language == 'es':
        st.info(f"📋 **Tipos de archivo soportados:** {', '.join(supported_types)}")
    else:
        st.info(f"📋 **Supported file types:** {', '.join(supported_types)}")

# File uploader
uploaded_file = st.file_uploader(
    upload_label,
    type=supported_types if INGEST_AVAILABLE else ['pdf', 'txt', 'docx', 'md'],
    accept_multiple_files=False,
    help=f"Límite: 100MB. Tipos soportados: {', '.join(supported_types) if INGEST_AVAILABLE else 'PDF, TXT, DOCX, MD'}"
)

if st.button(add_button_text):
    if uploaded_file:
        logger.info(f"File upload initiated: {uploaded_file.name}")
        if INGEST_AVAILABLE:
            # Validate file first
            is_valid, validation_message = validate_uploaded_file(uploaded_file)
            logger.info(f"File validation result for {uploaded_file.name}: {is_valid}")

            if is_valid:
                # Additional security checks
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                max_size_mb = 100  # 100MB limit

                if file_size_mb > max_size_mb:
                    st.error(f"❌ El archivo es demasiado grande: {file_size_mb:.1f}MB. Límite máximo: {max_size_mb}MB" if current_language == 'es' else f"❌ File is too large: {file_size_mb:.1f}MB. Maximum limit: {max_size_mb}MB")
                else:
                    # Check for suspicious file patterns
                    filename = uploaded_file.name.lower()
                    suspicious_patterns = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.jar', '.zip', '.rar', '.7z']
                    is_suspicious = any(pattern in filename for pattern in suspicious_patterns)

                    if is_suspicious:
                        st.warning(f"⚠️ El archivo '{uploaded_file.name}' tiene una extensión potencialmente peligrosa. ¿Estás seguro de que quieres procesarlo?" if current_language == 'es' else f"⚠️ The file '{uploaded_file.name}' has a potentially dangerous extension. Are you sure you want to process it?")

                        if st.button("🔓 Procesar archivo de todos modos" if current_language == 'es' else "🔓 Process file anyway", type="secondary"):
                            process_file = True
                        else:
                            st.info("✅ Procesamiento cancelado por seguridad" if current_language == 'es' else "✅ Processing cancelled for security")
                            process_file = False
                    else:
                        process_file = True

                    if process_file:
                        try:
                            # State 1: Iniciando proceso
                            st.info("🔄 Iniciando proceso..." if current_language == 'es' else "🔄 Starting process...")
                            time.sleep(0.5)

                            # State 2: Archivo seguro
                            st.success("✅ Archivo seguro..." if current_language == 'es' else "✅ File secure...")
                            time.sleep(0.5)

                            # Process the file
                            result = ingest_file(uploaded_file, uploaded_file.name)

                            # State 3: Agregado
                            if result and result.get("success"):
                                # Get domain information from the result if available
                                domain_info = ""
                                if result.get("domain"):
                                    domain_info = f" (Dominio: {result.get('domain')})"
                                elif result.get("collection"):
                                    domain_info = f" (Colección: {result.get('collection')})"

                                logger.info(f"File processed successfully: {uploaded_file.name}{domain_info}")
                                current_language = get_session_state_value('language', 'es')
                                st.success(f"✅ {success_message}: {uploaded_file.name}{domain_info}" if current_language == 'es' else f"✅ {success_message}: {uploaded_file.name}{domain_info}")
                                # Trigger refresh by bumping nonce
                                current_nonce = get_session_state_value('files_refresh_nonce', 0)
                                set_session_state_value('files_refresh_nonce', current_nonce + 1)
                            else:
                                error_msg = result.get("error", "Error desconocido") if result else "Sin resultado"
                                logger.error(f"File processing failed: {uploaded_file.name} - {error_msg}")
                                st.error(f"❌ {error_message}: {error_msg}" if current_language == 'es' else f"❌ {error_message}: {error_msg}")

                        except Exception as e:
                                error_details = str(e)
                                if "Connection" in error_details or "timeout" in error_details.lower():
                                    st.error(f"❌ {error_message}: Error de conexión. Verifica la configuración de la base de datos." if current_language == 'es' else f"❌ {error_message}: Connection error. Please check database configuration.")
                                elif "Permission" in error_details or "access" in error_details.lower():
                                    st.error(f"❌ {error_message}: Error de permisos. Verifica los permisos de escritura en la base de datos." if current_language == 'es' else f"❌ {error_message}: Permission error. Please check database write permissions.")
                                elif "Memory" in error_details or "out of memory" in error_details.lower():
                                    st.error(f"❌ {error_message}: Error de memoria. El archivo podría ser demasiado grande." if current_language == 'es' else f"❌ {error_message}: Memory error. The file might be too large.")
                                else:
                                    st.error(f"❌ {error_message}: {error_details}" if current_language == 'es' else f"❌ {error_message}: {error_details}")
                                if show_checkbox("Mostrar detalles técnicos" if current_language == 'es' else "Show technical details", key="show_error_details"):
                                    show_code(f"Error: {type(e).__name__}: {error_details}", language="text")
            else:
                st.error(f"❌ {validation_message}")
        else:
            st.error("❌ Sistema de ingesta no disponible")
    else:
        st.warning(f"⚠️ {upload_first_message}")

# -------------------------------
# NUEVO: Listado real desde Chroma
# -------------------------------
markdown_html(f'<h3 class="files-title">{files_table_title}</h3>')

def _collect_files_from_chroma(max_per_collection: int = 2000):
    rows = []
    try:
        cols = CHROMA_CLIENT.list_collections()
    except Exception as e:
        st.error(f"Error listando colecciones: {e}")
        return rows

    for c in cols:
        try:
            col = CHROMA_CLIENT.get_or_create_collection(c.name)
            # Preferir traer solo metadatos para no cargar documentos completos
            try:
                res = col.get(include=["metadatas"], limit=max_per_collection)  # type: ignore
            except Exception:
                res = col.get(limit=max_per_collection)
        except Exception as e2:
            st.warning(f"No se pudo leer la colección '{c.name}': {e2}")
            continue

        metadatas = (res or {}).get("metadatas", []) or []
        ids = (res or {}).get("ids", []) or []

        for i, meta in enumerate(metadatas):
            if isinstance(meta, dict):
                rows.append({
                    "collection": c.name,
                    "uploaded_file_name": meta.get("uploaded_file_name"),
                    "file_hash": meta.get("file_hash"),
                    "domain": meta.get("domain"),
                    "size_bytes": meta.get("file_size"),
                    "id": ids[i] if i < len(ids) else None,
                })
    return rows

@st.cache_data(ttl=15)
def _get_files_df(_nonce: int = 0):
    data = _collect_files_from_chroma()
    if not data:
        return pd.DataFrame(columns=["collection","uploaded_file_name","file_hash","domain","size_bytes","id"])
    df = pd.DataFrame(data)
    # Quitar filas sin nombre de archivo (p.ej. embeddings internos)
    df = df[df["uploaded_file_name"].notna()]
    # Deduplicar por (collection, file_hash) si hay hash
    if "file_hash" in df.columns:
        df = df.sort_values(["collection","uploaded_file_name"]).drop_duplicates(["collection","file_hash"], keep="last")
    return df

# Barra de acciones de listado
topA, topB = st.columns([1,3])
with topA:
    if st.button("🔄 Actualizar", type="secondary"):
        # Forzar recarga inmediata invalidando cache y moviendo el nonce
        _get_files_df.clear()
        current_nonce = get_session_state_value('files_refresh_nonce', 0)
        set_session_state_value('files_refresh_nonce', current_nonce + 1)
with topB:
    st.caption("Lista de archivos detectados en todas las colecciones de Chroma.")

# Nonce para invalidar cache tras ingesta/eliminación
nonce = get_session_state_value('files_refresh_nonce', 0)
files_df = _get_files_df(nonce)

if INGEST_AVAILABLE:
    try:
        if not files_df.empty:
            # Filtros de búsqueda
            st.subheader("🔍 Filtros de búsqueda" if current_language == 'es' else "🔍 Search filters")

            col1, col2 = st.columns(2)

            with col1:
                # Dominio
                available_domains = sorted(files_df['domain'].dropna().unique().tolist())
                domain_options = (['Todos los dominios'] if current_language == 'es' else ['All domains']) + available_domains
                selected_domain = st.selectbox(
                    "Dominio:" if current_language == 'es' else "Domain:",
                    options=domain_options,
                    index=0,
                    key="domain_filter"
                )

            with col2:
                # Colección
                available_collections = sorted(files_df['collection'].dropna().unique().tolist())
                collection_options = (['Todas las colecciones'] if current_language == 'es' else ['All collections']) + available_collections
                selected_collection = st.selectbox(
                    "Colección:" if current_language == 'es' else "Collection:",
                    options=collection_options,
                    index=0,
                    key="collection_filter"
                )

            def apply_filter(df, filter_value, filter_column, all_values_text):
                if filter_value != all_values_text:
                    return df[df[filter_column] == filter_value]
                return df

            all_domains_text = 'Todos los dominios' if current_language == 'es' else 'All domains'
            all_collections_text = 'Todas las colecciones' if current_language == 'es' else 'All collections'

            filtered_df = files_df.copy()
            filtered_df = apply_filter(filtered_df, selected_domain, 'domain', all_domains_text)
            filtered_df = apply_filter(filtered_df, selected_collection, 'collection', all_collections_text)

            # Estado de filtros
            active_filters = []
            if selected_domain != all_domains_text:
                active_filters.append(f"dominio '{selected_domain}'")
            if selected_collection != all_collections_text:
                active_filters.append(f"colección '{selected_collection}'")

            if active_filters:
                filter_text = " y ".join(active_filters) if current_language == 'es' else " and ".join(active_filters)
                st.info(f"📊 Mostrando {len(filtered_df)} archivos de {filter_text}" if current_language == 'es' else f"📊 Showing {len(filtered_df)} files from {filter_text}")
            else:
                st.info(f"📊 Mostrando todos los {len(filtered_df)} archivos" if current_language == 'es' else f"📊 Showing all {len(filtered_df)} files")

            # Estadísticas (solo cuando no hay filtros activos)
            if (selected_domain == all_domains_text and selected_collection == all_collections_text):
                st.subheader("📈 Estadísticas por dominio y colección" if current_language == 'es' else "📈 Domain and collection statistics")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Por Dominio:**" if current_language == 'es' else "**By Domain:**")
                    domain_stats = files_df.groupby('domain', dropna=True).size().reset_index(name='count')
                    domain_stats.columns = ['Dominio', 'Archivos'] if current_language == 'es' else ['Domain', 'Files']
                    domain_stats = domain_stats.sort_values(domain_stats.columns[-1], ascending=False)
                    for domain_label, domain_count in domain_stats.itertuples(index=False, name=None):
                        show_metric(
                            label=domain_label,
                            value=domain_count
                        )

                with col2:
                    st.markdown("**Por Colección:**" if current_language == 'es' else "**By Collection:**")
                    collection_stats = files_df.groupby('collection', dropna=True).size().reset_index(name='count')
                    collection_stats.columns = ['Colección', 'Archivos'] if current_language == 'es' else ['Collection', 'Files']
                    collection_stats = collection_stats.sort_values(collection_stats.columns[-1], ascending=False)
                    for collection_label, collection_count in collection_stats.itertuples(index=False, name=None):
                        show_metric(
                            label=collection_label,
                            value=collection_count
                        )

            # Búsqueda
            search_query = get_text_input(
                "🔍 Buscar archivos:" if current_language == 'es' else "🔍 Search files:",
                placeholder="Escribe para buscar..." if current_language == 'es' else "Type to search...",
                key="file_search",
                help="Busca por nombre de archivo, dominio o colección" if current_language == 'es' else "Search by filename, domain, or collection"
            )

            if search_query and search_query.strip():
                sq = search_query.strip()
                import re
                pat = re.compile(re.escape(sq), re.IGNORECASE)
                search_df = filtered_df[
                    filtered_df['uploaded_file_name'].astype(str).str.contains(pat, na=False, regex=True) |
                    filtered_df['domain'].astype(str).str.contains(pat, na=False, regex=True) |
                    filtered_df['collection'].astype(str).str.contains(pat, na=False, regex=True)
                ].copy()
                if len(search_df) == 0:
                    st.warning(f"⚠️ No se encontraron archivos que coincidan con '{sq}'" if current_language == 'es' else f"⚠️ No files found matching '{sq}'")
                else:
                    st.info(f"🔍 Encontrados {len(search_df)} archivos que coinciden con '{sq}'" if current_language == 'es' else f"🔍 Found {len(search_df)} files matching '{sq}'")
            else:
                search_df = filtered_df.copy()

            # Tabla
            display_df = search_df[['uploaded_file_name', 'domain', 'collection']].copy()
            display_df.columns = ['Archivo', 'Dominio', 'Colección'] if current_language == 'es' else ['File', 'Domain', 'Collection']

            if len(display_df) > 50:
                st.info(f"📊 Mostrando {len(display_df)} archivos. Considera usar los filtros para reducir el número de resultados." if current_language == 'es' else f"📊 Showing {len(display_df)} files. Consider using filters to reduce the number of results.")

            page_size = 25
            total_pages = (len(display_df) + page_size - 1) // page_size

            if total_pages > 1:
                page_number = st.selectbox(
                    "Página:" if current_language == 'es' else "Page:",
                    options=list(range(1, total_pages + 1)),
                    index=0,
                    key="files_page"
                )
                start_idx = (page_number - 1) * page_size
                end_idx = min(start_idx + page_size, len(display_df))
                display_page_df = display_df.iloc[start_idx:end_idx].copy()
                st.dataframe(display_page_df, width='stretch', hide_index=True)
                show_caption(f"Mostrando {start_idx + 1}-{end_idx} de {len(display_df)} archivos" if current_language == 'es' else f"Showing {start_idx + 1}-{end_idx} of {len(display_df)} files")
            else:
                st.dataframe(display_df, width='stretch', hide_index=True)

            # Eliminar archivo
            st.subheader("🗑️ Eliminar archivo" if current_language == 'es' else "🗑️ Delete file")
            if not filtered_df.empty:
                file_to_delete = st.selectbox(
                    "Seleccionar archivo para eliminar:" if current_language == 'es' else "Select file to delete:",
                    options=sorted(filtered_df['uploaded_file_name'].dropna().unique().tolist()),
                    key="file_to_delete"
                )

                if file_to_delete:
                    st.warning(f"⚠️ **Atención:** Se eliminará permanentemente el archivo '{file_to_delete}' de la base de datos." if current_language == 'es' else f"⚠️ **Warning:** The file '{file_to_delete}' will be permanently deleted from the database.")

                    col1, col2 = st.columns(2)
                    with col1:
                        confirm_delete = st.button(
                            "✅ Confirmar eliminación" if current_language == 'es' else "✅ Confirm deletion",
                            type="primary",
                            help="Eliminar permanentemente el archivo" if current_language == 'es' else "Permanently delete the file"
                        )
                    with col2:
                        cancel_delete = st.button(
                            "❌ Cancelar" if current_language == 'es' else "❌ Cancel",
                            type="secondary",
                            help="Cancelar la eliminación" if current_language == 'es' else "Cancel deletion"
                        )

                    if confirm_delete:
                        with st.spinner("Eliminando archivo..." if current_language == 'es' else "Deleting file..."):
                            try:
                                success = delete_file_from_vectordb(file_to_delete)
                                if success:
                                    st.success(f"✅ Archivo eliminado exitosamente: {file_to_delete}" if current_language == 'es' else f"✅ File successfully deleted: {file_to_delete}")
                                    # Forzar refresco
                                    _get_files_df.clear()
                                    current_nonce = get_session_state_value('files_refresh_nonce', 0)
                                    set_session_state_value('files_refresh_nonce', current_nonce + 1)
                                else:
                                    st.error(f"❌ No se pudo eliminar el archivo: {file_to_delete}" if current_language == 'es' else f"❌ Could not delete file: {file_to_delete}")
                            except Exception as e:
                                st.error(f"❌ Error al eliminar archivo: {str(e)}" if current_language == 'es' else f"❌ Error deleting file: {str(e)}")

                    if cancel_delete:
                        st.info("✅ Eliminación cancelada" if current_language == 'es' else "✅ Deletion cancelled")
        else:
            st.info(f"📂 {no_files_message}")
    except Exception as e:
        st.error(f"❌ Error al obtener archivos: {str(e)}")
        st.info(f"📂 {no_files_message}")
else:
    st.info(f"📂 {no_files_message}")
