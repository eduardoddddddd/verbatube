# Verbatube

Base de datos local de subtítulos de YouTube con visualizador web.
Sin servidores externos, sin APIs de pago. Todo local.

## Requisitos

```bash
pip install yt-dlp
```

## Estructura

```
verbatube/
├── server.py             # Servidor local (reemplaza http.server) + API de descarga
├── downloader.py         # Descarga subtítulos de canal/playlist/vídeo
├── indexer.py            # Construye el índice JSON de búsqueda
├── viewer.html           # Visualizador web (SPA completa)
├── verbatube.json        # Índice generado (se crea al indexar)
└── subtitles/            # Junction → C:\Users\Edu\VTTs (carpeta común de VTTs)
```

## Carpeta común de VTTs

Todos los subtítulos se almacenan en `C:\Users\Edu\VTTs\` organizados por canal:

```
C:\Users\Edu\VTTs\
├── Isabel Pareja Astrología terapéutica y evolutiva\
├── MERCEDES - The Astral Method\
├── TuLunayTu\
└── Ursula Cosmic\
```

Esta carpeta es compartida con otros proyectos (AstroExtracto).
La variable `CORPUS_DIR` en `server.py`, `indexer.py` y `downloader.py` apunta siempre aquí.


## Uso paso a paso

### 1. Arrancar el servidor (siempre primero)

```bash
cd C:\Users\Edu\Verbatube
python server.py
```

Abre automáticamente: **http://localhost:8080/viewer.html**

> ⚠️ Usar siempre `server.py` en lugar de `python -m http.server`.
> Si se modifica cualquier `.py`, matar el proceso y relanzar.

### 2. Descargar desde el viewer

Pestaña **"+ Descargar"** → introducir URL → seleccionar idioma → Iniciar descarga.
El log aparece en tiempo real. Al terminar, recarga automáticamente la biblioteca.

### 3. Descargar desde línea de comandos

```bash
# Canal entero
python downloader.py --channel "https://www.youtube.com/@canal"

# Playlist
python downloader.py --playlist "https://www.youtube.com/playlist?list=PLxxx"

# Vídeo individual
python downloader.py --video "https://www.youtube.com/watch?v=xxxxx"

# Solo español
python downloader.py --channel "URL" --lang es
```

### 4. Reindexar manualmente

```bash
python indexer.py            # Incremental (solo nuevos)
python indexer.py --rebuild  # Reconstruir desde cero
```


## Funcionalidades del visualizador

- **Búsqueda full-text** en tiempo real sobre el texto de todos los subtítulos
- **Filtro por canal** e idioma
- **Vista limpia** — párrafos agrupados por pausas, sin timestamps, fuente grande
- **Vista con timestamps** — cada fragmento enlaza al minuto exacto en YouTube
- **Búsqueda dentro del vídeo** — navegación entre coincidencias con Enter
- **Deduplicación ASR** — elimina las repeticiones de ventana deslizante de YouTube
- **Pestaña Descargar** — descarga + reindexación con log en tiempo real

## Notas técnicas

- El `verbatube.json` incluye el texto completo de cada vídeo para búsqueda (~50KB/vídeo).
- La indexación es incremental: solo procesa VTTs nuevos o modificados (compara mtime).
- Los subtítulos automáticos ASR tienen calidad variable pero son suficientes para búsqueda.
- El servidor expone tres endpoints: `/api/download`, `/api/reindex`, `/api/log`.
- La junction `subtitles/` permite al viewer servir los VTTs como archivos estáticos.

## Problemas conocidos y soluciones

| Problema | Causa | Solución |
|---|---|---|
| Vídeo descargado no aparece en biblioteca | Servidor desactualizado | Reiniciar `server.py` |
| Error al indexar | `CORPUS_DIR` fuera de `BASE_DIR` | Ya corregido (v1.1) |
| Texto muy repetido | Subtítulos ASR con ventana deslizante | Deduplicación activa en viewer |

---

## Autoría

**Eduardo Abdul Malik Arias**
Ingeniero en Informática · Consultor SAP Basis · Órgiva, Granada
Concepción, diseño y dirección del proyecto.

**Claude Sonnet 4.6** — *Anthropic*
Modelo de lenguaje de propósito general (familia Claude 4).
Desarrollo de código, arquitectura y documentación.

> *Este proyecto nació de una conversación. La idea es humana; la implementación, colaborativa.*
