# La Edad de Hielo — Short animado

Short vertical (1080x1920, 30 fps, 67 s) de storytelling animado en 2D, sincronizado palabra a palabra con la narración original.

- Video final: `output/la_edad_de_hielo_short.mp4` (el audio original se copia sin recodificar)
- `src/lib.py`: motor de dibujo (skia): personajes articulados, mamut, lobos, oso, fuego, escenarios, interfaz
- `src/scenes.py`: 24 escenas con cámara, transiciones y tiempos sacados de la transcripción
- `src/render.py`: compositor (transiciones whip/punch/iris/wipe/fade), subtítulos karaoke, render multiproceso + ffmpeg
- `src/transcript_raw.json`: transcripción con tiempos por palabra (faster-whisper)

Renderizar: `pip install skia-python numpy` y `python3 src/render.py`
Previsualizar fotogramas: `python3 src/render.py --frames 12.5 40`

Fuentes: Luckiest Guy y Bangers (SIL OFL).
