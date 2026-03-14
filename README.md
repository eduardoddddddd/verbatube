# Verbatube

Base de datos local de subtítulos de YouTube con visualizador web.
Sin servidores externos, sin APIs de pago. Todo local y offline.

## Requisitos

```bash
pip install yt-dlp
```

## Instalación en un PC/Mac nuevo

### 1. Clona el repositorio

```bash
git clone https://github.com/eduardoddddddd/verbatube.git
cd verbatube
```

### 2. Configura la ruta de tus VTTs

Abre los tres archivos siguientes y cambia `CORPUS_DIR` a la ruta donde quieres guardar los subtítulos:

**`server.py`** (línea ~17):
```python
CORPUS_DIR = Path(r"C:\Users\Edu\VTTs")   # ← cambia esto
```

**`indexer.py`** (línea ~20):
```python
CORPUS_DIR = Path(r"C:\Users\Edu\VTTs")   # ← cambia esto
```

**`downloader.py`** (línea ~17):
```python
CORPUS_DIR = Path(r"C:\Users\Edu\VTTs")   # ← cambia esto
```

**Ejemplos por sistema:**
- Windows: `Path(r"C:\Users\TuUsuario\VTTs")`
- Mac/Linux: `Path("/Users/tuusuario/VTTs")` o `Path.home() / "VTTs"`

> Esta es la **única configuración necesaria**. El resto funciona igual en cualquier sistema.

### 3. Arranca el servidor

```bash
python server.py
```

Se abre automáticamente en: **http://localhost:8080/viewer.html**


## Uso diario

### Descargar un canal o vídeo

**Opción A — desde el propio viewer** (recomendado):
Pestaña **"+ Descargar"** → URL → Iniciar descarga → log en tiempo real → recarga automática.

**Opción B — línea de comandos:**
```bash
python downloader.py --channel "https://www.youtube.com/@canal"
python downloader.py --playlist "https://www.youtube.com/playlist?list=PLxxx"
python downloader.py --video "https://www.youtube.com/watch?v=xxxxx"
python downloader.py --channel "URL" --lang es        # solo español
python downloader.py --channel "URL" --lang es,en     # español + inglés
```

Tras la descarga, el indexer se lanza automáticamente desde el viewer.
Si se usa la línea de comandos, ejecutar también:
```bash
python indexer.py             # incremental (solo nuevos)
python indexer.py --rebuild   # reconstruir todo desde cero
```

## Estructura del proyecto

```
verbatube/
├── server.py       # Servidor local (arrancar siempre con esto)
├── downloader.py   # Descarga subtítulos de YouTube vía yt-dlp
├── indexer.py      # Construye el índice JSON de búsqueda
├── viewer.html     # Interfaz web (SPA completa)
└── verbatube.json  # Índice generado — NO subir a git
```

Los VTTs se guardan en `CORPUS_DIR` (configurable), organizados por canal:
```
VTTs/
├── Canal A/
│   ├── 20240101_VIDEOID_Título.es.vtt
│   └── 20240101_VIDEOID_Título.info.json
└── Canal B/
    └── ...
```

## Funcionalidades del visualizador

- Búsqueda full-text en tiempo real sobre el texto de todos los subtítulos
- Filtro por canal e idioma
- Vista limpia (párrafos agrupados, sin timestamps)
- Vista con timestamps (cada fragmento enlaza al minuto exacto en YouTube)
- Búsqueda dentro del vídeo activo con navegación entre coincidencias
- Deduplicación del ASR de YouTube (elimina las repeticiones típicas)
- Pestaña Descargar con log en tiempo real

## Notas importantes

- **Arrancar siempre con `python server.py`**, no con `python -m http.server`.
  Si se modifica cualquier `.py`, reiniciar el servidor.
- `verbatube.json` puede pesar bastante (≈50 KB por vídeo). Está en `.gitignore`.
- Algunos vídeos de YouTube no tienen subtítulos automáticos — en ese caso
  solo se descarga el `.info.json` sin `.vtt` y no aparecen en el viewer.
- La indexación es incremental: solo procesa VTTs nuevos o modificados.

---

## Autoría

**Eduardo Abdul Malik Arias**
Ingeniero en Informática · Consultor SAP Basis · Órgiva, Granada
Concepción, diseño y dirección del proyecto.

**Claude Sonnet 4.6** — *Anthropic*
Modelo de lenguaje de propósito general (familia Claude 4).
Desarrollo de código, arquitectura y documentación.

> *Este proyecto nació de una conversación. La idea es humana; la implementación, colaborativa.*
