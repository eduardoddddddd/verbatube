#!/usr/bin/env python3
"""
Verbatube - Downloader
Descarga subtítulos de canales, playlists o vídeos individuales de YouTube
usando yt-dlp. Sin descarga de vídeo. Incremental (no repite lo ya descargado).

Uso:
    python downloader.py --channel "https://www.youtube.com/@canal"
    python downloader.py --playlist "https://www.youtube.com/playlist?list=PLxxx"
    python downloader.py --video "https://www.youtube.com/watch?v=xxxxx"
    python downloader.py --channel "https://www.youtube.com/@canal" --lang es,en
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Directorios
BASE_DIR   = Path(__file__).parent
CORPUS_DIR = Path(r"C:\Users\Edu\VTTs")   # Carpeta común para todos los proyectos

CORPUS_DIR.mkdir(exist_ok=True)


def check_ytdlp():
    """Comprueba que yt-dlp está instalado."""
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        print(f"[OK] yt-dlp {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("[ERROR] yt-dlp no encontrado. Instala con: pip install yt-dlp")
        sys.exit(1)


def get_already_downloaded():
    """Devuelve set de video_ids ya descargados."""
    existing = set()
    for f in CORPUS_DIR.rglob("*.vtt"):
        # Formato: VIDEO_ID.LANG.vtt  o  VIDEO_ID.LANG.srv3  etc.
        parts = f.stem.split(".")
        if len(parts) >= 2:
            existing.add(parts[0])
    return existing


def download_subtitles(url: str, langs: list[str], skip_existing: bool = True):
    """
    Descarga subtítulos usando yt-dlp.
    
    Args:
        url: URL del canal, playlist o vídeo
        langs: Lista de idiomas, e.g. ["es", "en"]
        skip_existing: Si True, omite vídeos ya descargados
    """
    check_ytdlp()
    
    already_downloaded = get_already_downloaded() if skip_existing else set()
    if already_downloaded:
        print(f"[INFO] {len(already_downloaded)} vídeos ya descargados, se omitirán")

    lang_str = ",".join(langs)

    cmd = [
        "yt-dlp",
        "--skip-download",               # Solo metadatos + subtítulos, sin vídeo
        "--write-subs",                  # Subtítulos manuales
        "--write-auto-subs",             # Subtítulos automáticos (YouTube ASR)
        "--sub-langs", lang_str,         # Idiomas
        "--sub-format", "vtt",           # Formato VTT (mejor que SRT para timestamps)
        "--write-info-json",             # Metadatos del vídeo en JSON
        "--no-overwrites",               # No sobreescribir si existe
        "--output", str(CORPUS_DIR / "%(channel)s" / "%(upload_date)s_%(id)s_%(title)s.%(ext)s"),
        "--restrict-filenames",          # Evita caracteres raros en nombres
        "--ignore-errors",               # Continúa si falla un vídeo
        "--no-playlist-reverse",         # Mantiene orden cronológico
        url
    ]

    # Si hay vídeos ya descargados, añadir exclusiones
    # yt-dlp soporta --match-filters pero lo más simple es --no-overwrites
    # Para exclusión real usamos archive
    archive_file = BASE_DIR / "download_archive.txt"
    cmd += ["--download-archive", str(archive_file)]

    print(f"\n[START] Descargando subtítulos de: {url}")
    print(f"[INFO] Idiomas: {lang_str}")
    print(f"[INFO] Destino: {SUBTITLES_DIR}\n")

    try:
        subprocess.run(cmd, check=False)  # check=False porque --ignore-errors
        print(f"\n[DONE] Descarga completada")
        print(f"[INFO] Ejecuta ahora: python indexer.py")
    except KeyboardInterrupt:
        print("\n[ABORTED] Descarga interrumpida por el usuario")


def main():
    parser = argparse.ArgumentParser(
        description="Verbatube Downloader - Descarga subtítulos de YouTube"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--channel", help="URL del canal de YouTube")
    group.add_argument("--playlist", help="URL de la playlist")
    group.add_argument("--video", help="URL de un vídeo individual")
    
    parser.add_argument(
        "--lang", 
        default="es,en",
        help="Idiomas de subtítulos separados por coma (default: es,en)"
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Volver a descargar aunque ya exista"
    )

    args = parser.parse_args()
    
    langs = [l.strip() for l in args.lang.split(",")]
    url = args.channel or args.playlist or args.video
    
    download_subtitles(url, langs, skip_existing=not args.no_skip)


if __name__ == "__main__":
    main()
