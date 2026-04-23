# Geo Report Generator

Generador de informes agronómicos para parcelas de viñedo a partir de:

- imágenes y estadísticas Sentinel Hub (Process + Statistical API),
- cartografía WMS (PNOA/IGN),
- plantillas HTML renderizadas a PDF con WeasyPrint.

El resultado principal es:

- `reports/informe_YYYY_MM.pdf`
- `reports/informe_YYYY_MM.json`

## Requisitos

- Python 3.10+
- Dependencias de `requirements.txt`
- Librerías de sistema necesarias para `gdal` y `weasyprint`

Instalación:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Crea o edita `src/.env` con:

```env
CDSE_CLIENT_ID=...
CDSE_CLIENT_SECRET=...

# API de IA compatible con OpenAI Chat Completions
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

## Estructura de entrada/salida

- GeoJSON de entrada: `geojson_entrada/*.geojson`  
  (si no hay archivo, usa `data/parcela_demo.geojson`)
- Assets generados por parcela: `assets/entregas/<ID>/<YYYY_MM>/...`
- Informes finales: `reports/`

## Ejecución

```bash
python3 src/report_generator.py
```

El proceso:

1. Lee parcelas del GeoJSON.
2. Descarga ortofoto/topográfico por WMS.
3. Pide a Sentinel Hub índices (`ndvi`, `ndre`, `ndmi`, `chl`) y estadísticas mensuales del último año.
4. Genera gráficas y compone el PDF.
5. Exporta un JSON completo con series mensuales y metadatos.

## Notas

- Si no existe `OPENAI_API_KEY`, el informe usa textos locales por defecto en la sección de interpretación.
- El JSON incluye:
  - `indices` con series completas por intervalo,
  - `datos_reales_ultimo_anio_mensual` por índice,
  - `summary_for_pdf` para la tabla resumida.
