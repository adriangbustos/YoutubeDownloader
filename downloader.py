import os
import sys
import re
import threading
import customtkinter as ctk
from tkinter import messagebox
import yt_dlp

# Configuracion de customtkinter
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, '_MEIPASS', PROJECT_ROOT)
else:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = PROJECT_ROOT

FFMPEG_PATH = os.path.join(PROJECT_ROOT, "ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = os.path.join(BUNDLE_DIR, "ffmpeg.exe")

FFPROBE_PATH = os.path.join(PROJECT_ROOT, "ffprobe.exe")
if not os.path.exists(FFPROBE_PATH):
    FFPROBE_PATH = os.path.join(BUNDLE_DIR, "ffprobe.exe")

QUALITY_OPTIONS = [
    "MP4 (1080p Full HD)",
    "MP4 (Mejor Calidad / Máxima Resolución)",
    "MP4 (Calidad Estándar 720p)",
    "MP3 (Audio 192 kbps)",
    "Solo Transcripción (.txt)",
]

def clean_subtitles_to_txt(directory):
    """Convierte subtítulos .vtt/.srt en texto plano limpio (.txt) y elimina cualquier archivo .vtt/.srt."""
    for filename in os.listdir(directory):
        if filename.endswith(".vtt") or filename.endswith(".srt"):
            sub_path = os.path.join(directory, filename)
            base_name = os.path.splitext(filename)[0]
            clean_name = re.sub(r'(\.[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*)+$', '', base_name)
            txt_path = os.path.join(directory, clean_name + ".txt")
            try:
                with open(sub_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                clean_lines = []
                prev_line = ""
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                        continue
                    if "-->" in line or line.isdigit():
                        continue
                    clean = re.sub(r'<[^>]+>', '', line).strip()
                    if clean and clean != prev_line:
                        clean_lines.append(clean)
                        prev_line = clean

                if clean_lines:
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(clean_lines))
            except Exception:
                pass
            finally:
                try:
                    if os.path.exists(sub_path):
                        os.remove(sub_path)
                except Exception:
                    pass

    # Barrido final garantizado: eliminar cualquier .vtt o .srt que haya quedado
    for filename in os.listdir(directory):
        if filename.endswith(".vtt") or filename.endswith(".srt"):
            try:
                os.remove(os.path.join(directory, filename))
            except Exception:
                pass


def resolve_single_sub_lang(url, ydl_opts_base):
    """Detecta el único idioma original real del video para evitar descargar traducciones o doblajes."""
    try:
        check_opts = dict(ydl_opts_base)
        check_opts['skip_download'] = True
        check_opts['writesubtitles'] = False
        check_opts['writeautomaticsub'] = False
        with yt_dlp.YoutubeDL(check_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            vid_lang = (info.get('language') or '').lower()
            base_lang = vid_lang.split('-')[0] if vid_lang else ''

            subs = info.get('subtitles', {})
            auto = info.get('automatic_captions', {})
            all_langs = list(subs.keys()) + list(auto.keys())

            # 1. Coincidencia exacta con idioma base del video y sufijo 'orig' (ej: 'en-orig')
            if base_lang:
                for l in all_langs:
                    if l.lower().startswith(base_lang) and 'orig' in l.lower():
                        return [l]
                for l in all_langs:
                    if l.lower().startswith(base_lang):
                        return [l]

            # 2. Preferir inglés o español original
            for preferred in ['en-orig', 'es-orig', 'en', 'es']:
                if preferred in all_langs:
                    return [preferred]

            # 3. Primer -orig disponible
            for l in all_langs:
                if 'orig' in l.lower():
                    return [l]

            if all_langs:
                return [all_langs[0]]
    except Exception:
        pass
    return ['en-orig']

def get_ydl_opts(formato_elegido, progress_hook=None, outtmpl=None, download_subs=False, output_dir=None):
    target_dir = output_dir or PROJECT_ROOT
    opts = {
        'outtmpl': outtmpl or os.path.join(target_dir, '%(title)s.%(ext)s'),
        'color': 'no_color',
        'windowsfilenames': True,
    }
    if progress_hook:
        opts['progress_hooks'] = [progress_hook]

    # Descarga unicamente el idioma original del video (evita 'too many requests' por traducciones)
    sub_langs = ['orig', '.*-orig']

    if "Solo Transcripción" in formato_elegido:
        opts['skip_download'] = True
        opts['writesubtitles'] = True
        opts['writeautomaticsub'] = True
        opts['subtitleslangs'] = sub_langs
    elif "Mejor Calidad" in formato_elegido or "best" in formato_elegido.lower():
        opts['format'] = 'bestvideo+bestaudio/best'
        opts['merge_output_format'] = 'mp4'
    elif "1080p" in formato_elegido:
        opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
        opts['merge_output_format'] = 'mp4'
    elif "720p" in formato_elegido:
        opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
        opts['merge_output_format'] = 'mp4'
    else:  # MP3 / Audio
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    if os.path.exists(FFMPEG_PATH):
        opts['ffmpeg_location'] = os.path.dirname(FFMPEG_PATH)

    cookies_path = os.path.join(PROJECT_ROOT, "cookies.txt")
    if os.path.exists(cookies_path):
        opts['cookiefile'] = cookies_path

    if download_subs:
        opts['writesubtitles'] = True
        opts['writeautomaticsub'] = True
        opts['subtitleslangs'] = sub_langs

    return opts


class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader Pro")
        self.geometry("650x600")
        self.resizable(False, False)

        icon_path = os.path.join(PROJECT_ROOT, "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(BUNDLE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        # Titulo
        self.title_label = ctk.CTkLabel(self, text="YouTube Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # Marco Principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Instruccion URLs
        self.url_label = ctk.CTkLabel(self.main_frame, text="Enlaces de YouTube (Uno por línea):", font=ctk.CTkFont(size=14))
        self.url_label.pack(anchor="w", padx=20, pady=(15, 5))

        # Caja de texto para multiples URLs
        self.url_textbox = ctk.CTkTextbox(self.main_frame, height=120, font=("Segoe UI", 12))
        self.url_textbox.pack(fill="x", padx=20)

        # Configuraciones (Calidad y Subtitulos)
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=20, pady=15)

        self.format_var = ctk.StringVar(value=QUALITY_OPTIONS[0])
        self.format_combo = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.format_var,
            values=QUALITY_OPTIONS,
            width=300
        )
        self.format_combo.pack(side="left", padx=(0, 10))

        self.subtitles_var = ctk.BooleanVar(value=False)
        self.subtitles_check = ctk.CTkCheckBox(
            self.options_frame, 
            text="Descargar Transcripciones",
            variable=self.subtitles_var
        )
        self.subtitles_check.pack(side="left")

        # Selector de carpeta destino
        self.folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.folder_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.output_dir_var = ctk.StringVar(value=PROJECT_ROOT)
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            textvariable=self.output_dir_var,
            font=("Segoe UI", 11),
            state="readonly"
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            self.folder_frame,
            text="Cambiar Carpeta...",
            command=self._select_folder,
            width=140
        )
        self.browse_btn.pack(side="right")

        # Boton Descargar
        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Iniciar Descarga",
            command=self.start_download,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#e62117",  # YouTube Red
            hover_color="#cc0000",
            height=40
        )
        self.download_btn.pack(pady=15)

        # Progreso
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, mode='determinate')
        self.progress_bar.pack(fill="x", padx=20, pady=5)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Esperando enlaces...", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=5)

        # Info del motor
        self.engine_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.engine_frame.pack(fill="x", pady=(0, 15))

        if os.path.exists(FFMPEG_PATH) and os.path.exists(FFPROBE_PATH):
            engine_text = "✅ Motor FFmpeg y FFprobe listos"
            engine_color = "green"
        else:
            engine_text = "⚠️ FFmpeg no detectado"
            engine_color = "#b35900"

        self.engine_label = ctk.CTkLabel(self.engine_frame, text=engine_text, text_color=engine_color, font=ctk.CTkFont(size=12))
        self.engine_label.pack(pady=(0, 2))

        if os.path.exists(os.path.join(PROJECT_ROOT, "cookies.txt")):
            self.cookie_label = ctk.CTkLabel(self.engine_frame, text="🍪 Sesión detectada (cookies.txt)", text_color="#1E90FF", font=ctk.CTkFont(size=12, weight="bold"))
            self.cookie_label.pack()

        self.is_downloading = False

    def _hook(self, d):
        if d['status'] == 'downloading':
            try:
                p_str = d.get('_percent_str')
                if p_str:
                    p_clean = re.sub(r'\x1b\[[0-9;]*m', '', p_str).replace('%', '').strip()
                    p = float(p_clean)
                else:
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    p = (downloaded / total * 100) if total > 0 else 0.0

                speed = d.get('_speed_str', 'N/A').strip()
                speed = re.sub(r'\x1b\[[0-9;]*m', '', speed)

                eta = d.get('_eta_str', 'N/A').strip()
                eta = re.sub(r'\x1b\[[0-9;]*m', '', eta)

                self.after(0, self._update_progress, p, speed, eta)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.after(0, self._on_download_finished_step)

    def _update_progress(self, p, speed, eta):
        self.progress_bar.set(p / 100.0)
        self.status_label.configure(text=f"Descargando [{self.current_idx}/{self.total_urls}]: {p:.1f}% | Vel: {speed} | ETA: {eta}")

    def _on_download_finished_step(self):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"Procesando y uniendo archivo [{self.current_idx}/{self.total_urls}]...")

    def _select_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if folder:
            self.output_dir_var.set(folder)

    def start_download(self):
        if self.is_downloading:
            return

        raw_urls = self.url_textbox.get("1.0", "end-1c").strip()
        if not raw_urls:
            messagebox.showerror("Error", "Por favor ingresa al menos una URL de YouTube.")
            return

        # Filtrar URLs vacias
        self.urls = [u.strip() for u in raw_urls.split('\n') if u.strip()]
        self.total_urls = len(self.urls)
        
        if self.total_urls == 0:
            return

        self.is_downloading = True
        self.download_btn.configure(state="disabled")
        self.progress_bar.set(0)

        formato_elegido = self.format_var.get()
        descargar_subs = self.subtitles_var.get()
        target_dir = self.output_dir_var.get()

        threading.Thread(target=self._run_queue, args=(formato_elegido, descargar_subs, target_dir), daemon=True).start()

    def _run_queue(self, formato_elegido, descargar_subs, target_dir):
        opts = get_ydl_opts(formato_elegido, progress_hook=self._hook, download_subs=descargar_subs, output_dir=target_dir)
        is_transcript_only = "Solo Transcripción" in formato_elegido
        needs_subs = is_transcript_only or descargar_subs

        for i, url in enumerate(self.urls, 1):
            self.current_idx = i
            self.after(0, lambda idx=i: self.status_label.configure(text=f"Iniciando descarga [{idx}/{self.total_urls}]..."))
            self.after(0, lambda: self.progress_bar.set(0))
            
            cur_opts = dict(opts)
            if needs_subs:
                cur_opts['subtitleslangs'] = resolve_single_sub_lang(url, opts)

            try:
                with yt_dlp.YoutubeDL(cur_opts) as ydl:
                    ydl.download([url])
                if needs_subs:
                    clean_subtitles_to_txt(target_dir)
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda idx=i, err=err_msg: messagebox.showerror("Error", f"Ocurrió un error con el enlace {idx}:\n{err}"))
                
        self.after(0, self._on_all_finished)

    def _on_all_finished(self):
        self.is_downloading = False
        self.download_btn.configure(state="normal")
        self.status_label.configure(text="¡Todas las descargas han finalizado exitosamente!")
        self.progress_bar.set(0)
        messagebox.showinfo("Éxito", "¡Cola de descargas completada!")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
