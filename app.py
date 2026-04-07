"""
Descargador Universal de Videos - app.py
========================================
Aplicación Streamlit para descargar videos de Instagram, YouTube y TikTok.
Utiliza yt-dlp como motor de descarga unificado para las 3 plataformas.

Autor: Auto-generado
Versión: 2.0
"""

import streamlit as st
import yt_dlp
import os
import re
import shutil
import tempfile
import time
import glob
from pathlib import Path


# --- CONSTANTES ---
APP_TITLE = "📲 Video Downloader Pro"
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")

# Patrones de URL para detección automática de plataforma
PLATFORM_PATTERNS = {
    "Instagram": [
        r"(https?://)?(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_-]+",
        r"(https?://)?(www\.)?instagr\.am/(p|reel|tv)/[A-Za-z0-9_-]+",
    ],
    "YouTube": [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]+",
        r"(https?://)?(www\.)?youtube\.com/shorts/[A-Za-z0-9_-]+",
        r"(https?://)?(www\.)?youtu\.be/[A-Za-z0-9_-]+",
        r"(https?://)?m\.youtube\.com/watch\?v=[A-Za-z0-9_-]+",
    ],
    "TikTok": [
        r"(https?://)?(www\.|vm\.)?tiktok\.com/@[^/]+/video/\d+",
        r"(https?://)?(www\.|vm\.)?tiktok\.com/[A-Za-z0-9_-]+",
        r"(https?://)?vm\.tiktok\.com/[A-Za-z0-9_-]+",
    ],
}


def detect_platform(url: str) -> str | None:
    """
    Detecta automáticamente la plataforma basándose en la URL proporcionada.

    Args:
        url: URL del video a analizar.

    Returns:
        Nombre de la plataforma detectada ('Instagram', 'YouTube', 'TikTok')
        o None si no se reconoce.
    """
    if not url:
        return None
    url = url.strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return None


def get_platform_icon(platform: str) -> str:
    """
    Retorna el icono emoji correspondiente a cada plataforma.

    Args:
        platform: Nombre de la plataforma.

    Returns:
        Emoji string representando la plataforma.
    """
    icons = {
        "Instagram": "📸",
        "YouTube": "▶️",
        "TikTok": "🎵",
    }
    return icons.get(platform, "🌐")


def get_platform_color(platform: str) -> str:
    """
    Retorna el color hexadecimal asociado a cada plataforma.

    Args:
        platform: Nombre de la plataforma.

    Returns:
        Color hexadecimal como string.
    """
    colors = {
        "Instagram": "#E1306C",
        "YouTube": "#FF0000",
        "TikTok": "#00F2EA",
    }
    return colors.get(platform, "#666666")


def download_video(url: str, platform: str) -> dict:
    """
    Descarga un video utilizando yt-dlp con configuración optimizada por plataforma.

    Args:
        url: URL del video a descargar.
        platform: Plataforma detectada ('Instagram', 'YouTube', 'TikTok').

    Returns:
        Diccionario con 'success' (bool), 'path' (str o None),
        'title' (str o None), 'error' (str o None).
    """
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # Configuración base común
        options = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title).80s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }

        # Configuración específica por plataforma
        if platform == "Instagram":
            options.update({
                'format': 'best[ext=mp4]/best',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })
        elif platform == "YouTube":
            options.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })
        elif platform == "TikTok":
            options.update({
                'format': 'best[ext=mp4]/best',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'Video')
            video_path = ydl.prepare_filename(info)

            # Asegurar extensión .mp4
            if not video_path.endswith('.mp4'):
                mp4_path = os.path.splitext(video_path)[0] + '.mp4'
                if os.path.exists(mp4_path):
                    video_path = mp4_path

            if os.path.exists(video_path):
                return {
                    'success': True,
                    'path': video_path,
                    'title': video_title,
                    'error': None,
                }
            else:
                # Buscar cualquier archivo mp4 reciente en la carpeta
                mp4_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp4"))
                if mp4_files:
                    latest = max(mp4_files, key=os.path.getmtime)
                    return {
                        'success': True,
                        'path': latest,
                        'title': video_title,
                        'error': None,
                    }
                return {
                    'success': False,
                    'path': None,
                    'title': None,
                    'error': 'No se encontró el archivo descargado.',
                }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Private" in error_msg or "login" in error_msg.lower():
            return {
                'success': False, 'path': None, 'title': None,
                'error': '🔒 Este video es privado o requiere inicio de sesión. '
                         'Solo se pueden descargar videos públicos.',
            }
        elif "not available" in error_msg.lower():
            return {
                'success': False, 'path': None, 'title': None,
                'error': '🚫 Este video no está disponible. Puede haber sido eliminado '
                         'o restringido en tu región.',
            }
        return {
            'success': False, 'path': None, 'title': None,
            'error': f'Error de descarga: {error_msg}',
        }
    except Exception as e:
        return {
            'success': False, 'path': None, 'title': None,
            'error': f'Error inesperado: {str(e)}',
        }


def cleanup_downloads():
    """Elimina todos los archivos de la carpeta de descargas."""
    try:
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR)
            return True
    except Exception:
        return False
    return False


def inject_custom_css():
    """
    Inyecta CSS personalizado para un diseño premium con glassmorphism,
    gradientes y micro-animaciones.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* --- Variables de color --- */
    :root {
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-instagram: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
        --gradient-youtube: linear-gradient(135deg, #FF0000 0%, #CC0000 100%);
        --gradient-tiktok: linear-gradient(135deg, #00F2EA 0%, #FF0050 100%);
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.12);
        --shadow-glow: 0 0 40px rgba(102, 126, 234, 0.15);
    }

    /* --- Global --- */
    .stApp {
        font-family: 'Inter', sans-serif !important;
    }

    /* --- Hero Header --- */
    .hero-header {
        text-align: center;
        padding: 2rem 1rem 1.5rem;
        margin-bottom: 1.5rem;
        background: var(--gradient-primary);
        border-radius: 20px;
        box-shadow: var(--shadow-glow);
        position: relative;
        overflow: hidden;
    }

    .hero-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.3;
    }

    .hero-header h1 {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.3rem !important;
        position: relative;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .hero-header p {
        color: rgba(255,255,255,0.85) !important;
        font-size: 1rem !important;
        font-weight: 400 !important;
        position: relative;
        max-width: 500px;
        margin: 0 auto;
    }

    /* --- Platform Cards --- */
    .platform-cards {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin: 1.5rem 0;
        flex-wrap: wrap;
    }

    .platform-card {
        padding: 12px 24px;
        border-radius: 16px;
        text-align: center;
        font-weight: 600;
        font-size: 0.9rem;
        color: white;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        min-width: 100px;
    }

    .platform-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
    }

    .card-instagram { background: var(--gradient-instagram); }
    .card-youtube { background: var(--gradient-youtube); }
    .card-tiktok { background: var(--gradient-tiktok); color: #111 !important; }

    /* --- Detection badge --- */
    .detection-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.95rem;
        margin: 0.5rem 0 1rem;
        animation: fadeSlideIn 0.4s ease-out;
    }

    .badge-instagram {
        background: linear-gradient(135deg, rgba(225, 48, 108, 0.15), rgba(188, 24, 136, 0.15));
        color: #E1306C;
        border: 1px solid rgba(225, 48, 108, 0.3);
    }

    .badge-youtube {
        background: linear-gradient(135deg, rgba(255, 0, 0, 0.12), rgba(204, 0, 0, 0.12));
        color: #FF0000;
        border: 1px solid rgba(255, 0, 0, 0.25);
    }

    .badge-tiktok {
        background: linear-gradient(135deg, rgba(0, 242, 234, 0.12), rgba(255, 0, 80, 0.12));
        color: #00C9BD;
        border: 1px solid rgba(0, 242, 234, 0.3);
    }

    /* --- Status container --- */
    .status-container {
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        animation: fadeSlideIn 0.5s ease-out;
    }

    .status-success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
        border: 1px solid rgba(16, 185, 129, 0.25);
    }

    .status-error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
        border: 1px solid rgba(239, 68, 68, 0.25);
    }

    /* --- Animations --- */
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    .downloading-pulse {
        animation: pulse 1.5s infinite;
    }

    /* --- Download button override --- */
    .stDownloadButton > button {
        background: var(--gradient-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* --- Main download button --- */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: var(--gradient-primary) !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.7rem 2rem !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.35) !important;
    }

    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.5) !important;
    }

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1c2e 0%, #16182b 100%) !important;
    }

    section[data-testid="stSidebar"] * {
        color: rgba(255, 255, 255, 0.85) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: white !important;
        font-weight: 700 !important;
    }

    /* --- Footer --- */
    .app-footer {
        text-align: center;
        padding: 1.5rem 0 1rem;
        color: rgba(150, 150, 150, 0.6);
        font-size: 0.8rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(150, 150, 150, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)


def render_hero():
    """Renderiza el header principal con gradiente."""
    st.markdown("""
    <div class="hero-header">
        <h1>📲 Video Downloader Pro</h1>
        <p>Descarga videos de Instagram, YouTube y TikTok en un solo clic</p>
    </div>
    """, unsafe_allow_html=True)


def render_platform_cards():
    """Renderiza las tarjetas de plataformas soportadas."""
    st.markdown("""
    <div class="platform-cards">
        <div class="platform-card card-instagram">📸 Instagram</div>
        <div class="platform-card card-youtube">▶️ YouTube</div>
        <div class="platform-card card-tiktok">🎵 TikTok</div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Renderiza el sidebar con guía rápida y opciones de limpieza."""
    with st.sidebar:
        st.markdown("### 💡 Guía Rápida")
        st.markdown("""
        1. **Pega el enlace** del video en el campo principal
        2. La plataforma se **detecta automáticamente**
        3. Presiona **"Descargar Video"**
        4. Espera unos segundos y **descarga el MP4**
        """)

        st.divider()

        st.markdown("### 🌐 Plataformas")
        st.markdown("""
        - **Instagram**: Reels, Posts, IGTV
        - **YouTube**: Videos, Shorts
        - **TikTok**: Videos públicos
        """)

        st.divider()

        st.markdown("### 🧹 Limpieza")
        if st.button("🗑️ Eliminar archivos descargados", use_container_width=True):
            if cleanup_downloads():
                st.success("✅ Archivos eliminados")
            else:
                st.info("No hay archivos para eliminar")

        st.divider()

        st.markdown("""
        <div style='font-size: 0.8rem; opacity: 0.6; text-align: center; padding-top: 1rem;'>
            ⚠️ Solo para uso personal y educativo.<br>
            Respeta los derechos de autor.
        </div>
        """, unsafe_allow_html=True)


def main():
    """
    Función principal de la aplicación Streamlit.
    Configura la página, inyecta estilos, renderiza la UI y maneja la descarga.
    """
    # --- Configuración de la página ---
    st.set_page_config(
        page_title="Video Downloader Pro",
        page_icon="📲",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    # --- Estilos y Layout ---
    inject_custom_css()
    render_hero()
    render_platform_cards()
    render_sidebar()

    # --- Input de URL ---
    st.markdown("")  # Spacer
    url = st.text_input(
        "🔗 Pega el enlace del video aquí:",
        placeholder="https://www.instagram.com/reel/... o youtube.com/watch?v=... o tiktok.com/...",
        key="video_url_input",
    )

    # --- Detección automática de plataforma ---
    detected_platform = detect_platform(url)

    if url and detected_platform:
        icon = get_platform_icon(detected_platform)
        badge_class = f"badge-{detected_platform.lower()}"
        st.markdown(
            f'<div class="detection-badge {badge_class}">'
            f'{icon} Plataforma detectada: <strong>{detected_platform}</strong></div>',
            unsafe_allow_html=True,
        )
    elif url and not detected_platform:
        st.warning("⚠️ No se pudo detectar la plataforma. Verifica que el enlace sea válido.")

    # --- Botón de descarga ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        download_clicked = st.button(
            "📥 Descargar Video",
            use_container_width=True,
            type="primary",
            key="download_button",
        )

    # --- Proceso de descarga ---
    if download_clicked:
        if not url:
            st.warning("⚠️ Por favor, pega un enlace de video primero.")
        elif not detected_platform:
            st.error("❌ Enlace no reconocido. Soportamos Instagram, YouTube y TikTok.")
        else:
            icon = get_platform_icon(detected_platform)
            progress_placeholder = st.empty()
            progress_placeholder.markdown(
                f'<div class="status-container downloading-pulse" '
                f'style="background: linear-gradient(135deg, rgba(102,126,234,0.1), '
                f'rgba(118,75,162,0.05)); border: 1px solid rgba(102,126,234,0.2);">'
                f'<p style="margin:0; font-weight:600;">'
                f'{icon} Descargando desde {detected_platform}...</p>'
                f'<p style="margin:0.3rem 0 0; font-size:0.85rem; opacity:0.7;">'
                f'Esto puede tomar unos segundos, por favor espera.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

            result = download_video(url, detected_platform)

            progress_placeholder.empty()

            if result['success'] and result['path']:
                st.markdown(
                    f'<div class="status-container status-success">'
                    f'<p style="margin:0; font-weight:600; color:#10B981;">'
                    f'✅ ¡Video descargado exitosamente!</p>'
                    f'<p style="margin:0.3rem 0 0; font-size:0.9rem;">'
                    f'📄 {result["title"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Mostrar video y botón de descarga
                try:
                    st.video(result['path'])
                except Exception:
                    st.info("Vista previa no disponible para este formato.")

                with open(result['path'], "rb") as f:
                    file_size = os.path.getsize(result['path'])
                    size_mb = file_size / (1024 * 1024)
                    st.download_button(
                        label=f"💾 Descargar MP4 ({size_mb:.1f} MB)",
                        data=f,
                        file_name=os.path.basename(result['path']),
                        mime="video/mp4",
                        key="download_file_button",
                    )
            else:
                st.markdown(
                    f'<div class="status-container status-error">'
                    f'<p style="margin:0; font-weight:600; color:#EF4444;">'
                    f'❌ Error en la descarga</p>'
                    f'<p style="margin:0.3rem 0 0; font-size:0.9rem;">'
                    f'{result["error"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # --- Footer ---
    st.markdown("""
    <div class="app-footer">
        Hecho con ❤️ usando Streamlit & yt-dlp · Solo para uso personal
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
