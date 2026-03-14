# Verbatube

Base de datos local de subtítulos de YouTube con visualizador web.  
Fork de astroextracto. Sin servidores externos, sin APIs de pago.

## Requisitos

```bash
pip install yt-dlp
```

## Estructura

```
verbatube/
├── downloader.py         # Descarga subtítulos de canal/playlist/vídeo
├── indexer.py            # Construye el índice JSON de búsqueda
├── viewer.html           # Visualizador web (abre en navegador)
├── verbatube.json        # Índice generado (se crea al indexar)
├── download_archive.txt  # Registro de descargas (incremental)
└── subtitles/            # Archivos VTT e info.json (generados)
```

## Uso paso a paso

### 1. Descargar subtítulos

```bash
# Canal entero
python downloader.py --channel "https://www.youtube.com/@canal"

# Playlist
python downloader.py --playlist "https://www.youtube.com/playlist?list=PLxxx"

# Vídeo individual
python downloader.py --video "https://www.youtube.com/watch?v=xxxxx"

# Solo en español
python downloader.py --channel "URL" --lang es

# Español + inglés (por defecto)
python downloader.py --channel "URL" --lang es,en
```

### 2. Indexar

```bash
python indexer.py

# Reconstruir desde cero (si hay cambios)
python indexer.py --rebuild
```

### 3. Visualizar

```bash
python -m http.server 8080
```

Abre en el navegador: **http://localhost:8080/viewer.html**

## Funcionalidades del visualizador

- **Búsqueda full-text**: busca dentro del texto de todos los subtítulos
- **Filtro por canal**: si tienes varios canales descargados
- **Filtro por idioma**: es / en
- **Vista limpia**: texto agrupado en párrafos legibles, sin timestamps
- **Vista con timestamps**: cada línea con su tiempo enlazado a YouTube
- **Búsqueda dentro del vídeo**: busca y navega entre coincidencias en el vídeo activo
- **Thumbnails**: carga las miniaturas de YouTube directamente

## Notas

- El archivo `verbatube.json` puede ser grande si tienes muchos vídeos  
  (estimación: ~10-20 KB por vídeo con texto incluido).
- La indexación es incremental: solo procesa los VTT nuevos o modificados.
- El `download_archive.txt` evita re-descargar vídeos ya procesados.
- Los subtítulos automáticos de YouTube (ASR) tienen calidad variable  
  pero suelen ser suficientes para búsqueda de contenido.

---

## Autoría

**Eduardo Abdul Malik Arias**  
Ingeniero en Informática · Consultor SAP Basis · Órgiva, Granada  
Concepción, diseño y dirección del proyecto.

**Claude Sonnet 4.6** — *Anthropic*  
Modelo de lenguaje de propósito general (familia Claude 4).  
Desarrollo de código, arquitectura y documentación.

> *Este proyecto nació de una conversación. La idea es humana; la implementación, colaborativa.*
