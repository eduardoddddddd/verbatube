#!/usr/bin/env python3
"""
Verbatube - Indexer
Lee los archivos VTT y JSON de metadatos descargados por downloader.py
y construye el índice maestro verbatube.json con el texto completo
para permitir búsqueda full-text en el visualizador.

Uso:
    python indexer.py
    python indexer.py --rebuild    # Reconstruye desde cero ignorando caché
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent
SUBTITLES_DIR = BASE_DIR / "subtitles"
INDEX_FILE = BASE_DIR / "verbatube.json"

# Máx. caracteres de texto para preview en la lista
PREVIEW_LENGTH = 280


def parse_vtt(vtt_path: Path) -> tuple[list[dict], str]:
    """
    Parsea un archivo WebVTT de YouTube.
    
    Returns:
        (cues, full_text)
        cues: lista de {start, end, text} con timestamps en segundos
        full_text: texto limpio sin duplicados ni timestamps
    """
    try:
        content = vtt_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] No se pudo leer {vtt_path.name}: {e}")
        return [], ""

    lines = content.split("\n")
    cues = []
    current_start = None
    current_end = None
    current_lines = []
    in_cue = False
    seen_texts = set()  # Para deduplicar líneas solapadas

    TIMESTAMP_RE = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    )
    # Tags de YouTube: <00:00:05.000>, <c>, </c>, <b>, etc.
    TAG_RE = re.compile(r"<[^>]+>")

    def ts_to_seconds(h, m, s, ms):
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

    def clean_text(text: str) -> str:
        text = TAG_RE.sub("", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    for line in lines:
        line = line.rstrip()

        # Detectar línea de timestamp
        m = TIMESTAMP_RE.match(line)
        if m:
            # Guardar cue anterior
            if current_start is not None and current_lines:
                text = " ".join(current_lines).strip()
                if text and text not in seen_texts:
                    cues.append({
                        "start": current_start,
                        "end": current_end,
                        "text": text
                    })
                    seen_texts.add(text)

            current_start = ts_to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
            current_end = ts_to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
            current_lines = []
            in_cue = True
            continue

        if in_cue:
            if line == "":
                # Fin del cue
                if current_lines:
                    text = " ".join(current_lines).strip()
                    if text and text not in seen_texts:
                        cues.append({
                            "start": current_start,
                            "end": current_end,
                            "text": text
                        })
                        seen_texts.add(text)
                in_cue = False
                current_lines = []
                current_start = None
            else:
                cleaned = clean_text(line)
                if cleaned and not re.match(r"^\d+$", cleaned):  # Ignorar números solos (índices SRT)
                    current_lines.append(cleaned)

    # Último cue sin línea en blanco final
    if current_lines and current_start is not None:
        text = " ".join(current_lines).strip()
        if text and text not in seen_texts:
            cues.append({
                "start": current_start,
                "end": current_end,
                "text": text
            })

    # Construir full_text: texto limpio, sin duplicados, separado por espacios
    full_text = " ".join(cue["text"] for cue in cues)
    # Normalizar espacios múltiples
    full_text = re.sub(r"\s+", " ", full_text).strip()

    return cues, full_text


def load_meta_json(video_id: str) -> dict:
    """Carga metadatos de yt-dlp (.info.json) si existe."""
    # yt-dlp guarda como VIDEO_ID.info.json en el mismo directorio
    meta_path = SUBTITLES_DIR / f"{video_id}.info.json"
    if meta_path.exists():
        try:
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def format_duration(seconds: float) -> str:
    """Convierte segundos a formato legible HH:MM:SS o MM:SS."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def build_index(rebuild: bool = False):
    """Construye o actualiza el índice maestro."""
    
    # Cargar índice existente para actualización incremental
    existing_index = {}
    if not rebuild and INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, encoding="utf-8") as f:
                data = json.load(f)
                for video in data.get("videos", []):
                    existing_index[video["video_id"]] = video
            print(f"[INFO] Índice existente: {len(existing_index)} vídeos")
        except Exception as e:
            print(f"[WARN] Error leyendo índice existente: {e}")

    # Encontrar todos los VTT disponibles
    # Formato de yt-dlp: VIDEO_ID.LANG.vtt o VIDEO_ID.LANG-auto.vtt
    vtt_files = list(SUBTITLES_DIR.glob("*.vtt"))
    
    if not vtt_files:
        print(f"[ERROR] No se encontraron archivos .vtt en {SUBTITLES_DIR}")
        print("[INFO] Ejecuta primero: python downloader.py --channel URL")
        sys.exit(1)

    # Agrupar VTTs por video_id (puede haber es + en por vídeo)
    videos_vtts: dict[str, list[Path]] = {}
    for vtt in vtt_files:
        # Extraer video_id: todo antes del primer punto de idioma
        # Ej: "dQw4w9WgXcQ.es.vtt" → "dQw4w9WgXcQ"
        stem = vtt.stem  # "dQw4w9WgXcQ.es"
        parts = stem.split(".")
        video_id = parts[0]
        videos_vtts.setdefault(video_id, []).append(vtt)

    print(f"[INFO] VTTs encontrados: {len(vtt_files)} de {len(videos_vtts)} vídeos")

    videos = []
    new_count = 0
    updated_count = 0

    for video_id, vtts in sorted(videos_vtts.items()):
        # Prioridad de idioma: es > en > primero disponible
        def lang_priority(p: Path):
            stem = p.stem
            if ".es" in stem: return 0
            if ".en" in stem: return 1
            return 2
        
        vtts_sorted = sorted(vtts, key=lang_priority)
        primary_vtt = vtts_sorted[0]
        
        # Detectar idioma del archivo primario
        lang_part = primary_vtt.stem.replace(video_id + ".", "")
        lang = lang_part.split("-")[0] if lang_part else "unknown"

        # Ruta relativa para el JSON (el viewer.html la usará)
        subtitle_file = str(primary_vtt.relative_to(BASE_DIR)).replace("\\", "/")

        # Comprobar si ya está indexado y el VTT no ha cambiado
        if video_id in existing_index and not rebuild:
            existing = existing_index[video_id]
            vtt_mtime = primary_vtt.stat().st_mtime
            if existing.get("_vtt_mtime") == vtt_mtime:
                videos.append(existing)
                continue

        # Parsear VTT
        print(f"  Indexando: {video_id} ({primary_vtt.name})")
        cues, full_text = parse_vtt(primary_vtt)

        if not full_text:
            print(f"    [WARN] Sin texto extraído, omitiendo")
            continue

        # Cargar metadatos de yt-dlp
        meta = load_meta_json(video_id)

        # Construir entrada del índice
        entry = {
            "video_id": video_id,
            "title": meta.get("title", video_id),
            "channel": meta.get("channel", meta.get("uploader", "Desconocido")),
            "channel_id": meta.get("channel_id", ""),
            "channel_url": meta.get("channel_url", ""),
            "published": meta.get("upload_date", ""),  # YYYYMMDD
            "duration_s": meta.get("duration", 0),
            "duration_fmt": format_duration(meta.get("duration", 0)),
            "thumbnail": meta.get("thumbnail", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "language": lang,
            "languages_available": [
                p.stem.replace(video_id + ".", "").split("-")[0]
                for p in vtts
            ],
            "subtitle_file": subtitle_file,
            "cue_count": len(cues),
            "text_preview": full_text[:PREVIEW_LENGTH] + ("…" if len(full_text) > PREVIEW_LENGTH else ""),
            "full_text": full_text,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "_vtt_mtime": primary_vtt.stat().st_mtime,
        }

        if video_id in existing_index:
            updated_count += 1
        else:
            new_count += 1

        videos.append(entry)

    # Ordenar por fecha de publicación (más reciente primero)
    def sort_key(v):
        return v.get("published", "") or ""
    
    videos.sort(key=sort_key, reverse=True)

    # Construir índice final
    channels = {}
    for v in videos:
        ch = v["channel"]
        if ch not in channels:
            channels[ch] = {
                "name": ch,
                "channel_id": v.get("channel_id", ""),
                "url": v.get("channel_url", ""),
                "count": 0
            }
        channels[ch]["count"] += 1

    index = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(videos),
        "channels": list(channels.values()),
        "videos": videos
    }

    # Guardar
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_kb = INDEX_FILE.stat().st_size / 1024
    print(f"\n[DONE] Índice guardado: {INDEX_FILE}")
    print(f"  Total vídeos: {len(videos)}")
    print(f"  Nuevos: {new_count} | Actualizados: {updated_count}")
    print(f"  Canales: {len(channels)}")
    print(f"  Tamaño JSON: {size_kb:.1f} KB")
    print(f"\n[NEXT] Abre el visualizador:")
    print(f"  cd {BASE_DIR} && python -m http.server 8080")
    print(f"  → http://localhost:8080/viewer.html")


def main():
    parser = argparse.ArgumentParser(
        description="Verbatube Indexer - Construye el índice de búsqueda"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Reconstruir índice desde cero (ignora caché)"
    )
    args = parser.parse_args()
    build_index(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
