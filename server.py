#!/usr/bin/env python3
"""
Verbatube - Server
Servidor local que reemplaza 'python -m http.server' y añade endpoints
para lanzar descarga e indexación desde el propio viewer.html.
Reutiliza la lógica yt-dlp ya probada en AstroExtracto.

Uso:
    python server.py
    → http://localhost:8080/viewer.html
"""

import http.server, subprocess, json, threading, os, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

BASE_DIR   = Path(__file__).parent
CORPUS_DIR = Path(r"C:\Users\Edu\VTTs")   # Carpeta común para todos los proyectos
PORT       = 8080

# Log en memoria para streaming
_log_lock   = threading.Lock()
_log_lines  = []
_running    = False

def log(msg):
    with _log_lock:
        _log_lines.append(msg)
    print(msg)

def reset_log():
    global _running
    with _log_lock:
        _log_lines.clear()
    _running = True

def get_log_since(offset):
    with _log_lock:
        return _log_lines[offset:], len(_log_lines), _running


def run_download_and_index(url, lang):
    """Ejecuta descarga e indexación en hilo aparte. Misma lógica que AstroExtracto."""
    global _running
    try:
        log(f"🚀 Iniciando descarga: {url}")
        log(f"   Idiomas: {lang}")
        log("─" * 50)

        # Comando yt-dlp — igual que AstroExtracto
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs",
            "--write-subs",
            "--sub-langs", lang,
            "--sub-format", "vtt",
            "--write-info-json",
            "--no-overwrites",
            "--ignore-errors",
            "--download-archive", str(BASE_DIR / "download_archive.txt"),
            "--output", str(CORPUS_DIR / "%(channel)s" / "%(upload_date)s_%(id)s_%(title)s.%(ext)s"),
            url
        ]

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", env=env
        )

        for line in proc.stdout:
            line = line.rstrip()
            if any(k in line for k in ["Downloading", "Writing", "already", "ERROR", "warning", "Finished"]):
                log(f"  {line}")

        proc.wait()
        log(f"\n✅ Descarga completada (código: {proc.returncode})")
        log("─" * 50)
        log("🗄️  Indexando...")

        # Lanzar indexer.py reutilizando el mismo proceso Python
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        idx = subprocess.Popen(
            [sys.executable, str(BASE_DIR / "indexer.py")],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=str(BASE_DIR), env=env
        )
        for line in idx.stdout:
            log(line.rstrip())
        idx.wait()

        log("\n🎉 ¡Todo listo! Recarga el viewer para ver los nuevos vídeos.")

    except Exception as e:
        log(f"❌ Error: {e}")
    finally:
        _running = False


class VerbaTubeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        pass  # Silenciar logs de peticiones estáticas

    def do_GET(self):
        parsed = urlparse(self.path)
        # Decodificar URL para manejar caracteres especiales (tildes, ñ, etc.)
        decoded_path = unquote(parsed.path, encoding='utf-8')
        params = parse_qs(parsed.query)

        # ── API: iniciar descarga ─────────────────────────────────────────────
        if decoded_path == "/api/download":
            if _running:
                self._json({"ok": False, "msg": "Ya hay una descarga en curso"})
                return
            url  = params.get("url", [""])[0].strip()
            lang = params.get("lang", ["es,en"])[0].strip()
            if not url:
                self._json({"ok": False, "msg": "URL vacía"})
                return
            reset_log()
            threading.Thread(target=run_download_and_index, args=(url, lang), daemon=True).start()
            self._json({"ok": True, "msg": "Descarga iniciada"})

        # ── API: leer log (polling) ───────────────────────────────────────────
        elif decoded_path == "/api/log":
            offset = int(params.get("offset", ["0"])[0])
            lines, total, running = get_log_since(offset)
            self._json({"lines": lines, "total": total, "running": running})

        # ── API: sólo reindexar ───────────────────────────────────────────────
        elif decoded_path == "/api/reindex":
            if _running:
                self._json({"ok": False, "msg": "Proceso en curso"})
                return
            reset_log()
            def do_index():
                global _running
                try:
                    idx = subprocess.Popen(
                        [sys.executable, str(BASE_DIR / "indexer.py")],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace", cwd=str(BASE_DIR)
                    )
                    for line in idx.stdout:
                        log(line.rstrip())
                    idx.wait()
                    log("🎉 Reindexación completada. Recarga el viewer.")
                finally:
                    _running = False
            threading.Thread(target=do_index, daemon=True).start()
            self._json({"ok": True, "msg": "Indexación iniciada"})

        # ── Archivos estáticos (viewer.html, subtitles/, etc.) ────────────────
        else:
            # Servir el archivo decodificando la ruta manualmente
            # Necesario en Windows para rutas con tildes/ñ/caracteres especiales
            file_path = BASE_DIR / decoded_path.lstrip('/')
            if file_path.is_file():
                self._serve_file(file_path)
            else:
                super().do_GET()

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path):
        """Sirve un archivo estático con detección de tipo MIME."""
        ext = file_path.suffix.lower()
        mime_types = {
            '.html': 'text/html; charset=utf-8',
            '.js':   'application/javascript; charset=utf-8',
            '.css':  'text/css; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.vtt':  'text/vtt; charset=utf-8',
            '.srt':  'text/plain; charset=utf-8',
            '.png':  'image/png',
            '.jpg':  'image/jpeg',
            '.ico':  'image/x-icon',
        }
        content_type = mime_types.get(ext, 'application/octet-stream')
        try:
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(data))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    print(f"✅ VerbaTube server en http://localhost:{PORT}/viewer.html")
    print(f"   Directorio: {BASE_DIR}")
    print("   Ctrl+C para detener\n")
    import webbrowser
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}/viewer.html")).start()
    with http.server.ThreadingHTTPServer(("", PORT), VerbaTubeHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
