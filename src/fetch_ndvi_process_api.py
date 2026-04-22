#!/usr/bin/env python3
"""
Sentinel Hub (Copernicus Data Space): raster (Process API) y estadísticas (Statistical API).

Modo viñedo: --preset bodegas y opcional --informe-mensual con --stats-json.
Flujo catastro → SIGPAC → PDF → email:  python3 fetch_ndvi_process_api.py --pipeline
Resumen técnico API:  python3 fetch_ndvi_process_api.py --info

Credenciales: .env con CDSE_CLIENT_ID y CDSE_CLIENT_SECRET (OAuth en
https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings).

Ejemplos:
  python3 fetch_ndvi_process_api.py --csv clientes.csv \\
    --from-date 2025-09-01T00:00:00Z --to-date 2025-09-30T23:59:59Z --out ./salidas
  python3 fetch_ndvi_process_api.py --lon -2.448 --lat 42.465 --id demo \\
    --radius-m 800 --from-date 2025-09-01T00:00:00Z --to-date 2025-09-30T23:59:59Z \\
    --format geotiff --style rgb --gsd-m 2.5 --out ./ndvi_salidas
  PNG con leyenda (NDVI/NDRE/NDMI/NDWI en rgb): añade --legend-png (matplotlib).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv
from osgeo import gdal
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

_ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_FILE)

DATA_MODEL_INFO = """
================================================================================
Qué datos obtiene este script y cómo (Sentinel Hub en Copernicus Data Space)
================================================================================

1) AUTENTICACIÓN
   - Tus credenciales OAuth2 (client id + secret) se leen de .env o del entorno.
   - El script pide un token JWT al Identity Server y reutiliza la sesión OAuth
     para todas las peticiones de la ejecución (no pidas un token por píxel).

2) PROCESS API  →  imagen georreferenciada por parcela (bbox)
   URL: POST .../api/v1/process
   Entrada que construye el script:
     - Límite rectangular (bbox) en WGS84 alrededor de lon/lat y --radius-m.
     - Colección S2 (--collection): L1C (TOA, por defecto) o L2A (corregida).
     - Ventana temporal en dataFilter (from / to).
     - Filtros opcionales: nubes máx., orden de mosaico, remuestreo BICUBIC/BILINEAR.
     - Un evalscript (JavaScript) que calcula el --index y devuelve RGB o float.
   Salida:
     - Un archivo por cliente: {id}_{index}.tif|.png|.jpg
     - GeoTIFF con georreferencia al bbox; es el mapa “para ver en QGIS”.

3) STATISTICAL API  →  números agregados sin bajar la imagen completa
   URL: POST .../statistics/v1
   Documentación: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Statistical.html
   Entrada:
     - Mismo bbox y colección que arriba; el tiempo va en "aggregation".
     - resx/resy en grados (~muestreo 10 m en suelo, aproximado desde la latitud).
     - --stats-interval (ej. P10D, P1M): trocea el periodo. P1M exige que el
       rango cubra mes(es) calendario completos: p. ej. septiembre 2025 con
       --to-date 2025-10-01T00:00:00Z (inicio del mes siguiente), no 30 sep 23:59.
       Por defecto el script usa P10D para evitar listas vacías con rangos típicos.
       El payload incluye lastIntervalBehavior=SHORTEN para el último trozo parcial.
     - Evalscript con salida "index" (valor del índice) + "dataMask" (obligatorio
       en Statistical API: qué píxeles entran en el cálculo).
   Salida (JSON en --stats-json):
     - Por cliente, status y lista "data" con un elemento por intervalo temporal.
     - En cada intervalo: outputs.index.bands.B0.stats con min, max, mean, stDev,
       sampleCount, noDataCount y percentiles (10, 25, 50, 75, 90).
     - Sirve para tablas de informe mensual, alertas, series por parcela, etc.

4) ÍNDICES --index (bandas Sentinel-2 vía Sentinel Hub; resolución nativa mezclada 10/20 m)
   ndvi      (B08,B04)           vigor vegetativo general
   ndre      (B08,B05)           clorofila / red edge, útil con dosel denso
   evi       (B02,B04,B08)       EVI estándar en reflectancia
   ndmi      (B08,B11)           índice de humedad Gao (NIR-SWIR) / estrés hídrico
   ndwi      (B03,B08)           NDWI McFeeters (agua / humedura superficial)
   bsi       (B02,B04,B08,B11)   suelo desnudo / baja cobertura
   scl       (SCL)               clasificación de escena L2A (nubes, sombras…); solo con L2A
   truecolor (B04,B03,B02)       vista RGB aproximada

5) L1C vs L2A
   - L1C: sin corrección atmosférica; suele parecerse más al Browser en RGB/índices simples.
   - L2A: reflectancia corregida; necesaria para SCL y análisis más físicos.

6) Modo bodegas (--preset bodegas)
   - Ajusta por defecto a Sentinel-2 L2A, índice NDRE en imagen y agregación P10D en stats
     (solo si no pasas explícitamente --collection, --index o --stats-interval).
   - Con --informe-mensual y --stats-json, el JSON incluye estadísticas de NDVI, NDRE y NDMI
     por parcela (además de la imagen del --index elegido, salvo --no-download).

Para la lista actual de flags:  python3 fetch_ndvi_process_api.py -h

7) Flujo informe bodega (objetivo de producto)
   Ver:  python3 fetch_ndvi_process_api.py --pipeline
================================================================================
""".strip()


PIPELINE_BODEGAS_INFO = """
================================================================================
Flujo propuesto: catastro / parcelas → satélite → SIGPAC → PDF → email
================================================================================

1) PARCELAS (origen de geometría)
   - Límite real: GeoJSON desde catastro/SIGPAC (EPSG:3857 Web Mercator es habitual)
     o WGS84. Pasa el archivo con --geojson; opcional --geojson-feature-index y
     --crs si el JSON no declara crs (RFC 7946).
   - Alternativa rápida: punto + --radius-m (--lon/--lat) para un bbox rectangular.
     Con --geojson se envía input.bounds.geometry + crs a Process y Statistical API.

2) SATÉLITE (este proyecto)
   - Process API → GeoTIFF del índice (p. ej. NDRE con --preset bodegas).
   - Statistical API → JSON mensual (--informe-mensual) con NDVI, NDRE, NDMI
     por parcela para tablas y cruces con otros datos.

3) QGIS
   - Cargar el raster descargado (ya georreferenciado al bbox o al polígono).
   - Cargar parcelas SIGPAC (WMS/WMTS del Ministerio, WFS, o capa local).
   - Alinear CRS; recortar o enmascarar el raster con el polígono de la parcela
     del cliente; opcional: composición con límites SIGPAC encima para el mapa final.
   - Automatizable con PyQGIS (plantilla de proyecto .qgz + script).

4) PDF
   - Diseño de impresión (layout) en QGIS exportando a PDF, o generación desde
     plantilla (ReportLab / WeasyPrint) si montáis informe fuera de QGIS.

5) EMAIL
   - Envío con SMTP (credenciales en .env), o API (SendGrid, SES, etc.) desde un
     script que adjunte el PDF y opcionalmente el JSON de estadísticas.

Orden práctico de implementación: (1) polígono en API → (2) PyQGIS batch → (3) PDF
→ (4) email. El punto (1) es el único cambio fuerte respecto al uso actual por punto.
================================================================================
""".strip()


TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
)
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
STATISTICS_URL = "https://sh.dataspace.copernicus.eu/statistics/v1"

PROCESS_INDEX_CHOICES = (
    "ndvi",
    "ndre",
    "evi",
    "ndmi",
    "ndwi",
    "bsi",
    "scl",
    "truecolor",
)

# Índices que van al JSON con --informe-mensual (tabla resumen mensual típica bodega)
INFORME_INDICES_ESTADISTICAS = ("ndvi", "ndre", "ndmi")

CRS84_URN = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
EPSG_3857_URN = "http://www.opengis.net/def/crs/EPSG/0/3857"


def _urn_for_epsg(code: str) -> str:
    c = code.upper().replace("EPSG:", "").strip()
    if c == "4326":
        return CRS84_URN
    return f"http://www.opengis.net/def/crs/EPSG/0/{c}"


def _geojson_legacy_crs_to_epsg(gj: dict) -> str | None:
    crs = gj.get("crs")
    if not crs or crs.get("type") != "name":
        return None
    name = (crs.get("properties") or {}).get("name", "")
    if "3857" in name:
        return "3857"
    if "4326" in name or "CRS84" in name.upper():
        return "4326"
    return None


def _iter_polygon_coords(geometry: dict):
    t = geometry.get("type")
    coords = geometry.get("coordinates")
    if t == "Polygon" and coords:
        for ring in coords:
            for pt in ring:
                yield float(pt[0]), float(pt[1])
    elif t == "MultiPolygon" and coords:
        for poly in coords:
            for ring in poly:
                for pt in ring:
                    yield float(pt[0]), float(pt[1])
    else:
        raise ValueError(f"Geometría no soportada: {t} (usa Polygon o MultiPolygon)")


def envelope_xy(geometry: dict) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for x, y in _iter_polygon_coords(geometry):
        xs.append(x)
        ys.append(y)
    if not xs:
        raise ValueError("Polígono sin coordenadas")
    return min(xs), min(ys), max(xs), max(ys)


def epsg3857_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Centro aproximado Web Mercator → lon/lat (suficiente para resolución stats en grados)."""
    lon = (x / 20037508.34) * 180.0
    lat = math.degrees(2.0 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2.0)
    return lon, lat


def centroid_lonlat_from_geometry(geometry: dict, epsg: str) -> tuple[float, float]:
    minx, miny, maxx, maxy = envelope_xy(geometry)
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    if epsg == "3857":
        return epsg3857_to_wgs84(cx, cy)
    return cx, cy


def _geometry_and_props_at(gj: dict, feature_index: int) -> tuple[dict, dict]:
    if gj.get("type") == "FeatureCollection":
        feats = gj.get("features") or []
        if not feats:
            raise ValueError("FeatureCollection sin features")
        if feature_index < 0 or feature_index >= len(feats):
            raise ValueError(f"feature index {feature_index} fuera de rango (0..{len(feats)-1})")
        feat = feats[feature_index]
        return feat["geometry"], feat.get("properties") or {}
    if gj.get("type") == "Feature":
        return gj["geometry"], gj.get("properties") or {}
    if gj.get("type") in ("Polygon", "MultiPolygon"):
        return gj, {}
    raise ValueError(f"Tipo GeoJSON no soportado: {gj.get('type')}")


def load_geojson_area(
    path: Path,
    feature_index: int,
    crs_override: str | None,
) -> tuple[dict, str, dict]:
    """
    Devuelve (geometry, crs_urn Sentinel Hub, properties del Feature).
    crs_override: ej. 3857 o EPSG:3857 si el GeoJSON no trae crs (RFC 7946).
    """
    raw = path.read_text(encoding="utf-8")
    try:
        gj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            "GeoJSON inválido (¿números pegados con 'JS:...' u otra basura?). "
            "Debe ser JSON válido. Detalle: "
            f"{e}"
        ) from e

    geom, props = _geometry_and_props_at(gj, feature_index)
    epsg = crs_override
    if epsg is not None:
        epsg = epsg.upper().replace("EPSG:", "").strip()
    if epsg is None:
        epsg = _geojson_legacy_crs_to_epsg(gj)
    if epsg is None:
        minx, miny, maxx, maxy = envelope_xy(geom)
        if abs(minx) <= 180 and abs(maxx) <= 180 and abs(miny) <= 90 and abs(maxy) <= 90:
            epsg = "4326"
        else:
            epsg = "3857"

    crs_urn = _urn_for_epsg(epsg)
    return geom, crs_urn, props


def dimensions_from_envelope_meters(
    width_m: float,
    height_m: float,
    gsd_m: float,
    max_side: int,
) -> tuple[int, int]:
    if gsd_m <= 0:
        raise ValueError("gsd_m debe ser > 0")
    w_px = max(64, min(max_side, int(math.ceil(width_m / gsd_m))))
    h_px = max(64, min(max_side, int(math.ceil(height_m / gsd_m))))
    return w_px, h_px


def stats_resolution_for_crs(crs_urn: str, lat_ref: float) -> tuple[float, float]:
    """resx/resy en unidades del CRS de bounds (grados si CRS84, metros si EPSG:3857)."""
    if "3857" in crs_urn:
        return 10.0, 10.0
    return stats_res_xy_degrees(lat_ref, 10.0)


def _sentinelhub_compliance_hook(response: requests.Response) -> requests.Response:
    response.raise_for_status()
    return response


def create_oauth_session() -> OAuth2Session:
    client_id = os.environ.get("CDSE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print(
            "Faltan CDSE_CLIENT_ID y/o CDSE_CLIENT_SECRET. "
            f"Define un archivo {_ENV_FILE} o exporta las variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    oauth.register_compliance_hook("access_token_response", _sentinelhub_compliance_hook)
    oauth.fetch_token(
        token_url=TOKEN_URL,
        client_secret=client_secret,
        include_client_id=True,
    )
    return oauth


def bbox_around_point(lon: float, lat: float, radius_m: float) -> tuple[float, float, float, float]:
    """BBox CRS84: minLon, minLat, maxLon, maxLat."""
    dlat = radius_m / 111_320.0
    cos_lat = max(math.cos(math.radians(lat)), 0.2)
    dlon = radius_m / (111_320.0 * cos_lat)
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def bbox_metric_size_m(bbox: tuple[float, float, float, float], lat_ref: float) -> tuple[float, float]:
    """Anchura y altura aproximadas del bbox en metros (CRS84)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    cos_lat = max(math.cos(math.radians(lat_ref)), 0.2)
    w_m = (max_lon - min_lon) * 111_320.0 * cos_lat
    h_m = (max_lat - min_lat) * 111_320.0
    return w_m, h_m


def dimensions_from_gsd(
    bbox: tuple[float, float, float, float],
    lat_ref: float,
    gsd_m: float,
    max_side: int,
) -> tuple[int, int]:
    """
    Píxeles de salida para acercarse a gsd_m metros por píxel en suelo.
    Valores menores de gsd_m => más píxeles y aspecto más nítido (hasta max_side).
    """
    if gsd_m <= 0:
        raise ValueError("--gsd-m debe ser > 0")
    w_m, h_m = bbox_metric_size_m(bbox, lat_ref)
    w_px = max(64, min(max_side, int(math.ceil(w_m / gsd_m))))
    h_px = max(64, min(max_side, int(math.ceil(h_m / gsd_m))))
    return w_px, h_px


def build_s2_data_entry(
    collection: str,
    time_from: str,
    time_to: str,
    *,
    resampling: str,
    max_cloud_coverage: int | None,
    mosaicking_order: str | None,
) -> dict:
    """Entrada `data[]` para Process API (incluye timeRange en dataFilter)."""
    data_filter: dict = {
        "timeRange": {
            "from": time_from,
            "to": time_to,
        },
    }
    if mosaicking_order:
        data_filter["mosaickingOrder"] = mosaicking_order
    if max_cloud_coverage is not None and 0 <= max_cloud_coverage < 100:
        data_filter["maxCloudCoverage"] = max_cloud_coverage
    return _apply_resampling_to_data_entry(
        {"type": collection, "dataFilter": data_filter},
        resampling,
    )


def build_s2_data_entry_statistics(
    collection: str,
    *,
    resampling: str,
    max_cloud_coverage: int | None,
    mosaicking_order: str | None,
) -> dict:
    """Entrada `data[]` para Statistical API (el tiempo va en `aggregation`, no aquí)."""
    data_filter: dict = {}
    if mosaicking_order:
        data_filter["mosaickingOrder"] = mosaicking_order
    if max_cloud_coverage is not None and 0 <= max_cloud_coverage < 100:
        data_filter["maxCloudCoverage"] = max_cloud_coverage
    return _apply_resampling_to_data_entry(
        {"type": collection, "dataFilter": data_filter},
        resampling,
    )


def _apply_resampling_to_data_entry(data_entry: dict, resampling: str) -> dict:
    if resampling == "smooth":
        data_entry["processing"] = {
            "upsampling": "BICUBIC",
            "downsampling": "BILINEAR",
        }
    elif resampling == "nearest":
        data_entry["processing"] = {
            "upsampling": "NEAREST",
            "downsampling": "NEAREST",
        }
    return data_entry


def stats_res_xy_degrees(lat_ref: float, meters: float = 10.0) -> tuple[float, float]:
    """resx/resy en grados para Statistical API con bbox CRS84 (~meters de muestreo)."""
    res_y = meters / 111_320.0
    res_x = meters / (111_320.0 * max(math.cos(math.radians(lat_ref)), 0.2))
    return res_x, res_y


EVALSCRIPT_NDVI_RGB = r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08"] }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let d = sample.B08 + sample.B04;
  let ndvi = d === 0 ? 0 : (sample.B08 - sample.B04) / d;
  if (ndvi < -0.5) return [0.05, 0.05, 0.05];
  if (ndvi < 0) return [0.92, 0.92, 0.92];
  if (ndvi < 0.025) return [1, 0.98, 0.8];
  if (ndvi < 0.1) return [0.86, 0.86, 0.55];
  if (ndvi < 0.2) return [0.66, 0.77, 0.4];
  if (ndvi < 0.3) return [0.47, 0.71, 0.32];
  if (ndvi < 0.4) return [0.27, 0.64, 0.24];
  if (ndvi < 0.5) return [0.13, 0.55, 0.22];
  return [0.05, 0.45, 0.15];
}
"""


EVALSCRIPT_NDVI_FLOAT32 = r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08"], units: "REFLECTANCE" }],
    output: { id: "default", bands: 1, sampleType: "FLOAT32" },
  };
}
function evaluatePixel(sample) {
  let d = sample.B08 + sample.B04;
  let ndvi = d === 0 ? 0 : (sample.B08 - sample.B04) / d;
  return [ndvi];
}
"""


def _ramp_vigor(v: str) -> str:
    """Fragmento JS: colorea un índice ~vegetación en [-1,1] a RGB."""
    return f"""
  let v = {v};
  if (v < -0.5) return [0.05, 0.05, 0.05];
  if (v < 0) return [0.92, 0.92, 0.92];
  if (v < 0.025) return [1, 0.98, 0.8];
  if (v < 0.1) return [0.86, 0.86, 0.55];
  if (v < 0.2) return [0.66, 0.77, 0.4];
  if (v < 0.3) return [0.47, 0.71, 0.32];
  if (v < 0.4) return [0.27, 0.64, 0.24];
  if (v < 0.5) return [0.13, 0.55, 0.22];
  return [0.05, 0.45, 0.15];
"""


EVALSCRIPT_TRUECOLOR = r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B03", "B02"], units: "REFLECTANCE" }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  // Realce visual para aproximar el aspecto del Copernicus Browser:
  // +ganancia, correccion gamma y ligera saturacion.
  let gain = 3.2;
  let gamma = 1.8;

  let r = Math.min(1, Math.max(0, sample.B04 * gain));
  let g = Math.min(1, Math.max(0, sample.B03 * gain));
  let b = Math.min(1, Math.max(0, sample.B02 * gain));

  r = Math.pow(r, 1.0 / gamma);
  g = Math.pow(g, 1.0 / gamma);
  b = Math.pow(b, 1.0 / gamma);

  // Saturacion suave para evitar tono apagado.
  let l = 0.3 * r + 0.59 * g + 0.11 * b;
  let s = 1.15;
  r = l + (r - l) * s;
  g = l + (g - l) * s;
  b = l + (b - l) * s;

  return [
    Math.min(1, Math.max(0, r)),
    Math.min(1, Math.max(0, g)),
    Math.min(1, Math.max(0, b))
  ];
}
"""


EVALSCRIPT_NDRE_RGB = (
    r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B05", "B08"] }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let d = sample.B08 + sample.B05;
  let ndre = d === 0 ? 0 : (sample.B08 - sample.B05) / d;
"""
    + _ramp_vigor("ndre")
    + r"""
}
"""
)


EVALSCRIPT_EVI_RGB = r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B04", "B08"], units: "REFLECTANCE" }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let L = sample.B08 + 6.0 * sample.B04 - 7.5 * sample.B02 + 1.0;
  let evi = L === 0 ? 0 : 2.5 * (sample.B08 - sample.B04) / L;
  if (evi < -1) return [0.05, 0.05, 0.05];
  if (evi < 0) return [0.85, 0.85, 0.85];
  if (evi < 0.2) return [0.9, 0.85, 0.5];
  if (evi < 0.4) return [0.55, 0.75, 0.35];
  if (evi < 0.6) return [0.25, 0.65, 0.22];
  return [0.05, 0.45, 0.12];
}
"""


EVALSCRIPT_NDMI_RGB = (
    r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B08", "B11"], units: "REFLECTANCE" }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let d = sample.B08 + sample.B11;
  let ndmi = d === 0 ? 0 : (sample.B08 - sample.B11) / d;
"""
    + _ramp_vigor("ndmi")
    + r"""
}
"""
)


EVALSCRIPT_NDWI_RGB = (
    r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B03", "B08"] }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let d = sample.B03 + sample.B08;
  let w = d === 0 ? 0 : (sample.B03 - sample.B08) / d;
"""
    + _ramp_vigor("w")
    + r"""
}
"""
)


EVALSCRIPT_BSI_RGB = r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B04", "B08", "B11"], units: "REFLECTANCE" }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let a = sample.B11 + sample.B04;
  let b = sample.B08 + sample.B02;
  let d = a + b;
  let bsi = d === 0 ? 0 : (a - b) / d;
  if (bsi < -0.5) return [0.05, 0.15, 0.05];
  if (bsi < 0) return [0.2, 0.45, 0.25];
  if (bsi < 0.2) return [0.55, 0.5, 0.25];
  if (bsi < 0.4) return [0.75, 0.55, 0.35];
  if (bsi < 0.6) return [0.85, 0.65, 0.45];
  return [0.92, 0.82, 0.72];
}
"""


EVALSCRIPT_SCL_RGB = r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["SCL"] }],
    output: { id: "default", bands: 3 },
  };
}
function evaluatePixel(sample) {
  let c = sample.SCL;
  if (c === 0 || c === 1 || c === 2) return [0.05, 0.05, 0.05];
  if (c === 3) return [0.35, 0.35, 0.35];
  if (c === 4) return [0.15, 0.55, 0.2];
  if (c === 5) return [0.35, 0.65, 0.25];
  if (c === 6) return [0.15, 0.35, 0.85];
  if (c === 7) return [0.85, 0.85, 0.2];
  if (c === 8) return [0.9, 0.5, 0.2];
  if (c === 9) return [0.75, 0.2, 0.75];
  if (c === 10) return [0.95, 0.95, 0.95];
  if (c === 11) return [0.4, 0.4, 0.95];
  return [0.1, 0.1, 0.1];
}
"""


def get_process_evalscript(index: str, style: str) -> str:
    if style == "raw" and index != "ndvi":
        raise ValueError("Solo el índice ndvi admite --style raw (GeoTIFF float32).")
    if index == "ndvi":
        return EVALSCRIPT_NDVI_RGB if style == "rgb" else EVALSCRIPT_NDVI_FLOAT32
    if index == "truecolor":
        return EVALSCRIPT_TRUECOLOR
    if index == "ndre":
        return EVALSCRIPT_NDRE_RGB
    if index == "evi":
        return EVALSCRIPT_EVI_RGB
    if index == "ndmi":
        return EVALSCRIPT_NDMI_RGB
    if index == "ndwi":
        return EVALSCRIPT_NDWI_RGB
    if index == "bsi":
        return EVALSCRIPT_BSI_RGB
    if index == "scl":
        return EVALSCRIPT_SCL_RGB
    raise ValueError(index)


def get_stats_evalscript(index: str) -> str:
    """Evalscript Statistical API: salida `index` + dataMask (obligatorio)."""
    if index == "ndvi":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "dataMask"], units: "REFLECTANCE" }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  let dm = sample.dataMask;
  let d = sample.B08 + sample.B04;
  let v = d === 0 ? 0 : (sample.B08 - sample.B04) / d;
  let m = dm * (d > 0 ? 1 : 0);
  return { index: [v], dataMask: [m] };
}
"""
    if index == "ndre":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B05", "B08", "dataMask"], units: "REFLECTANCE" }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  let dm = sample.dataMask;
  let d = sample.B08 + sample.B05;
  let v = d === 0 ? 0 : (sample.B08 - sample.B05) / d;
  return { index: [v], dataMask: [dm * (d > 0 ? 1 : 0)] };
}
"""
    if index == "evi":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B04", "B08", "dataMask"], units: "REFLECTANCE" }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  let dm = sample.dataMask;
  let L = sample.B08 + 6.0 * sample.B04 - 7.5 * sample.B02 + 1.0;
  let v = L === 0 ? 0 : 2.5 * (sample.B08 - sample.B04) / L;
  return { index: [v], dataMask: [dm * (Math.abs(L) > 1e-6 ? 1 : 0)] };
}
"""
    if index == "ndmi":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B08", "B11", "dataMask"], units: "REFLECTANCE" }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  let dm = sample.dataMask;
  let d = sample.B08 + sample.B11;
  let v = d === 0 ? 0 : (sample.B08 - sample.B11) / d;
  return { index: [v], dataMask: [dm * (d > 0 ? 1 : 0)] };
}
"""
    if index == "ndwi":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B03", "B08", "dataMask"] }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  let dm = sample.dataMask;
  let d = sample.B03 + sample.B08;
  let v = d === 0 ? 0 : (sample.B03 - sample.B08) / d;
  return { index: [v], dataMask: [dm * (d > 0 ? 1 : 0)] };
}
"""
    if index == "bsi":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B04", "B08", "B11", "dataMask"], units: "REFLECTANCE" }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  let dm = sample.dataMask;
  let a = sample.B11 + sample.B04;
  let b = sample.B08 + sample.B02;
  let d = a + b;
  let v = d === 0 ? 0 : (a - b) / d;
  return { index: [v], dataMask: [dm * (d > 0 ? 1 : 0)] };
}
"""
    if index == "scl":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["SCL", "dataMask"] }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  return { index: [sample.SCL], dataMask: [sample.dataMask] };
}
"""
    if index == "truecolor":
        return r"""
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "dataMask"] }],
    output: [
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}
function evaluatePixel(sample) {
  return { index: [sample.B04], dataMask: [sample.dataMask] };
}
"""
    raise ValueError(index)


def mime_for_format(fmt: str) -> str:
    if fmt == "geotiff":
        return "image/tiff"
    if fmt == "png":
        return "image/png"
    if fmt == "jpeg":
        return "image/jpeg"
    raise ValueError(fmt)


def build_payload(
    bbox: tuple[float, float, float, float],
    time_from: str,
    time_to: str,
    width: int,
    height: int,
    image_mime: str,
    evalscript: str,
    collection: str = "sentinel-2-l1c",
    *,
    resampling: str = "smooth",
    max_cloud_coverage: int | None = 90,
    mosaicking_order: str | None = "leastCC",
) -> dict:
    min_lon, min_lat, max_lon, max_lat = bbox
    data_entry = build_s2_data_entry(
        collection,
        time_from,
        time_to,
        resampling=resampling,
        max_cloud_coverage=max_cloud_coverage,
        mosaicking_order=mosaicking_order,
    )
    return {
        "input": {
            "bounds": {
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                },
            },
            "data": [data_entry],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": image_mime},
                }
            ],
        },
        "evalscript": evalscript,
    }


def build_payload_polygon(
    geometry: dict,
    crs_urn: str,
    time_from: str,
    time_to: str,
    width: int,
    height: int,
    image_mime: str,
    evalscript: str,
    collection: str = "sentinel-2-l1c",
    *,
    resampling: str = "smooth",
    max_cloud_coverage: int | None = 90,
    mosaicking_order: str | None = "leastCC",
) -> dict:
    data_entry = build_s2_data_entry(
        collection,
        time_from,
        time_to,
        resampling=resampling,
        max_cloud_coverage=max_cloud_coverage,
        mosaicking_order=mosaicking_order,
    )
    return {
        "input": {
            "bounds": {
                "geometry": geometry,
                "properties": {"crs": crs_urn},
            },
            "data": [data_entry],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": image_mime},
                }
            ],
        },
        "evalscript": evalscript,
    }


def post_process(
    oauth: OAuth2Session,
    payload: dict,
) -> tuple[bytes, str | None]:
    r = oauth.post(
        PROCESS_URL,
        json=payload,
        headers={"Accept": "*/*"},
    )
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower() or None
    return r.content, ctype


def build_statistics_payload(
    bbox: tuple[float, float, float, float],
    time_from: str,
    time_to: str,
    collection: str,
    evalscript: str,
    resx: float,
    resy: float,
    *,
    aggregation_interval: str,
    resampling: str,
    max_cloud_coverage: int | None,
    mosaicking_order: str | None,
) -> dict:
    min_lon, min_lat, max_lon, max_lat = bbox
    data_entry = build_s2_data_entry_statistics(
        collection,
        resampling=resampling,
        max_cloud_coverage=max_cloud_coverage,
        mosaicking_order=mosaicking_order,
    )
    return {
        "input": {
            "bounds": {
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                },
            },
            "data": [data_entry],
        },
        "aggregation": {
            "timeRange": {"from": time_from, "to": time_to},
            "aggregationInterval": {"of": aggregation_interval},
            # Sin esto, P1M/P10D con un rango que no encaja en intervalos completos
            # puede devolver "data": [] aunque status sea OK (comportamiento SKIP).
            "lastIntervalBehavior": "SHORTEN",
            "evalscript": evalscript,
            "resx": resx,
            "resy": resy,
        },
        "calculations": {
            "default": {
                "statistics": {
                    "default": {
                        "percentiles": {"k": [10, 25, 50, 75, 90]},
                    }
                }
            }
        },
    }


def build_statistics_payload_polygon(
    geometry: dict,
    crs_urn: str,
    time_from: str,
    time_to: str,
    collection: str,
    evalscript: str,
    resx: float,
    resy: float,
    *,
    aggregation_interval: str,
    resampling: str,
    max_cloud_coverage: int | None,
    mosaicking_order: str | None,
) -> dict:
    data_entry = build_s2_data_entry_statistics(
        collection,
        resampling=resampling,
        max_cloud_coverage=max_cloud_coverage,
        mosaicking_order=mosaicking_order,
    )
    return {
        "input": {
            "bounds": {
                "geometry": geometry,
                "properties": {"crs": crs_urn},
            },
            "data": [data_entry],
        },
        "aggregation": {
            "timeRange": {"from": time_from, "to": time_to},
            "aggregationInterval": {"of": aggregation_interval},
            "lastIntervalBehavior": "SHORTEN",
            "evalscript": evalscript,
            "resx": resx,
            "resy": resy,
        },
        "calculations": {
            "default": {
                "statistics": {
                    "default": {
                        "percentiles": {"k": [10, 25, 50, 75, 90]},
                    }
                }
            }
        },
    }


def post_statistics(oauth: OAuth2Session, payload: dict) -> dict:
    r = oauth.post(
        STATISTICS_URL,
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    r.raise_for_status()
    return r.json()


@dataclass
class Cliente:
    cliente_id: str
    lon: float
    lat: float
    geometry: dict | None = None
    crs_urn: str | None = None


def load_clientes_csv(path: Path) -> list[Cliente]:
    rows: list[Cliente] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV sin cabecera")
        fields = {h.strip().lower(): h for h in reader.fieldnames}
        for key in ("id", "lon", "lat"):
            if key not in fields:
                raise ValueError(
                    f"CSV debe incluir columnas id, lon, lat (encontrado: {reader.fieldnames})"
                )
        id_h, lon_h, lat_h = fields["id"], fields["lon"], fields["lat"]
        for row in reader:
            cid = (row.get(id_h) or "").strip()
            if not cid:
                continue
            rows.append(
                Cliente(
                    cliente_id=cid,
                    lon=float(row[lon_h]),
                    lat=float(row[lat_h]),
                )
            )
    return rows


def extension_for_format(fmt: str) -> str:
    return {"geotiff": "tif", "png": "png", "jpeg": "jpg"}[fmt]


# Misma rampa que _ramp_vigor en el evalscript (NDVI, NDRE, NDMI, NDWI en RGB).
_VIGOR_BOUNDARIES: tuple[float, ...] = (
    -1.0,
    -0.5,
    0.0,
    0.025,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    1.0,
)
_VIGOR_COLORS: tuple[tuple[float, float, float], ...] = (
    (0.05, 0.05, 0.05),
    (0.92, 0.92, 0.92),
    (1.0, 0.98, 0.8),
    (0.86, 0.86, 0.55),
    (0.66, 0.77, 0.4),
    (0.47, 0.71, 0.32),
    (0.27, 0.64, 0.24),
    (0.13, 0.55, 0.22),
    (0.05, 0.45, 0.15),
)
_VIGOR_INDICES = frozenset({"ndvi", "ndre", "ndmi", "ndwi"})
_INDEX_TITLE_ES: dict[str, str] = {
    "ndvi": "NDVI",
    "ndre": "NDRE",
    "ndmi": "NDMI",
    "ndwi": "NDWI",
}


def write_rgb_preview_with_legend(
    image_path: Path,
    index: str,
    *,
    style: str,
) -> Path | None:
    """
    Genera un PNG con la misma vista RGB y una leyenda de la rampa de vigor.
    Solo aplica a índices con rampa _ramp_vigor y salida RGB (--style rgb).
    Devuelve la ruta del PNG o None si no aplica.
    """
    if style != "rgb" or index not in _VIGOR_INDICES:
        return None
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import BoundaryNorm, ListedColormap
        import numpy as np
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "Para --legend-png instala: pip install matplotlib pillow numpy"
        ) from e

    img = Image.open(image_path)
    if img.mode not in ("RGB", "RGBA"):
        return None
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    arr = np.asarray(img)

    cmap = ListedColormap(list(_VIGOR_COLORS))
    norm = BoundaryNorm(list(_VIGOR_BOUNDARIES), cmap.N, clip=True)
    title = _INDEX_TITLE_ES.get(index, index.upper())
    w_px, h_px = img.size
    aspect = h_px / max(w_px, 1)
    fig_w = min(14.0, max(8.0, 10.0 * (w_px / max(h_px, 1))))
    fig_h = fig_w * aspect
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig, (ax_img, cax) = plt.subplots(
        1,
        2,
        figsize=(fig_w, fig_h),
        gridspec_kw={"width_ratios": [1, 0.07], "wspace": 0.12},
    )
    ax_img.imshow(arr, aspect="equal", interpolation="nearest")
    ax_img.set_axis_off()
    cb = fig.colorbar(sm, cax=cax, ticks=[-0.5, 0, 0.1, 0.2, 0.3, 0.4, 0.5])
    cb.set_label("Valor del índice", fontsize=10)
    cb.ax.tick_params(labelsize=9)
    fig.suptitle(
        f"{title} · escala de vigor (misma rampa que la API)",
        fontsize=11,
        y=0.995,
    )

    out = image_path.with_name(f"{image_path.stem}_leyenda.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", pad_inches=0.2, facecolor="white")
    plt.close(fig)
    return out


def fetch_for_cliente(
    oauth: OAuth2Session,
    c: Cliente,
    *,
    radius_m: float,
    time_from: str,
    time_to: str,
    width: int,
    height: int,
    out_format: str,
    out_dir: Path,
    collection: str,
    index: str,
    evalscript: str,
    resampling: str = "smooth",
    max_cloud_coverage: int | None = 90,
    mosaicking_order: str | None = "leastCC",
) -> Path:
    mime = mime_for_format(out_format)
    if c.geometry is not None and c.crs_urn is not None:
        payload = build_payload_polygon(
            c.geometry,
            c.crs_urn,
            time_from,
            time_to,
            width,
            height,
            mime,
            evalscript,
            collection=collection,
            resampling=resampling,
            max_cloud_coverage=max_cloud_coverage,
            mosaicking_order=mosaicking_order,
        )
    else:
        bbox = bbox_around_point(c.lon, c.lat, radius_m)
        payload = build_payload(
            bbox,
            time_from,
            time_to,
            width,
            height,
            mime,
            evalscript,
            collection=collection,
            resampling=resampling,
            max_cloud_coverage=max_cloud_coverage,
            mosaicking_order=mosaicking_order,
        )
    data, ctype = post_process(oauth, payload)
    ext = extension_for_format(out_format)
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in c.cliente_id)
    out_path = out_dir / f"{safe_id}_{index}.{ext}"
    out_path.write_bytes(data)
    return out_path


def clip_raster_to_geometry(
    raster_path: Path,
    geometry: dict,
    _crs_urn: str,
) -> Path:
    """
    Recorta el raster al polígono y añade alpha fuera de parcela.
    Sobrescribe el archivo de entrada preservando georreferencia.
    """
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": geometry}],
    }
    with tempfile.TemporaryDirectory(prefix="cutline_") as td:
        td_path = Path(td)
        cutline_path = td_path / "mask.geojson"
        clipped_path = td_path / "clipped.tif"
        cutline_path.write_text(json.dumps(feature_collection), encoding="utf-8")
        warp_options = gdal.WarpOptions(
            format="GTiff",
            cutlineDSName=str(cutline_path),
            cropToCutline=True,
            dstAlpha=True,
            multithread=True,
        )
        out_ds = gdal.Warp(str(clipped_path), str(raster_path), options=warp_options)
        if out_ds is None:
            raise RuntimeError("GDAL Warp devolvió None al recortar el raster")
        out_ds = None
        clipped_data = clipped_path.read_bytes()
    raster_path.write_bytes(clipped_data)
    return raster_path


def _argv_has_flag(argv_list: list[str], flag: str) -> bool:
    for a in argv_list:
        if a == flag or a.startswith(f"{flag}="):
            return True
    return False


def resolve_geojson_cliente_id(args: argparse.Namespace, props: dict, argv_list: list[str]) -> str:
    if _argv_has_flag(argv_list, "--id"):
        return args.id
    p = props
    keys = ("provincia", "municipio", "poligono", "parcela")
    if all(k in p for k in keys):
        return f"{p['provincia']}_{p['municipio']}_{p['poligono']}_{p['parcela']}"
    return args.id


def raster_size_for_cliente(c: Cliente, args: argparse.Namespace) -> tuple[int, int]:
    if c.geometry is None or c.crs_urn is None:
        bbox = bbox_around_point(c.lon, c.lat, args.radius_m)
        if args.gsd_m is not None:
            return dimensions_from_gsd(bbox, c.lat, args.gsd_m, args.max_side)
        return args.width, args.height
    minx, miny, maxx, maxy = envelope_xy(c.geometry)
    if "3857" in c.crs_urn:
        w_m, h_m = maxx - minx, maxy - miny
        if args.gsd_m is not None:
            return dimensions_from_envelope_meters(w_m, h_m, args.gsd_m, args.max_side)
        return args.width, args.height
    bbox_ll = (minx, miny, maxx, maxy)
    lat_ref = (miny + maxy) / 2.0
    if args.gsd_m is not None:
        return dimensions_from_gsd(bbox_ll, lat_ref, args.gsd_m, args.max_side)
    return args.width, args.height


def post_stats_for_index(
    oauth: OAuth2Session,
    c: Cliente,
    args: argparse.Namespace,
    max_cloud_arg: int | None,
    ix: str,
) -> dict:
    stats_eval = get_stats_evalscript(ix)
    rx, ry = stats_resolution_for_crs(c.crs_urn or CRS84_URN, c.lat)
    if c.geometry is not None and c.crs_urn is not None:
        stats_payload = build_statistics_payload_polygon(
            c.geometry,
            c.crs_urn,
            args.from_date,
            args.to_date,
            args.collection,
            stats_eval,
            rx,
            ry,
            aggregation_interval=args.stats_interval,
            resampling=args.resampling,
            max_cloud_coverage=max_cloud_arg,
            mosaicking_order=args.mosaicking_order,
        )
    else:
        bbox = bbox_around_point(c.lon, c.lat, args.radius_m)
        stats_payload = build_statistics_payload(
            bbox,
            args.from_date,
            args.to_date,
            args.collection,
            stats_eval,
            rx,
            ry,
            aggregation_interval=args.stats_interval,
            resampling=args.resampling,
            max_cloud_coverage=max_cloud_arg,
            mosaicking_order=args.mosaicking_order,
        )
    return post_statistics(oauth, stats_payload)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    epilog = """
Ejemplo imagen NDRE (Process API):
  python3 fetch_ndvi_process_api.py --lon -2.36575 --lat 42.46665 --id demo \\
    --radius-m 500 --index ndre \\
    --from-date 2025-09-01T00:00:00Z --to-date 2025-09-30T23:59:59Z \\
    --format geotiff --gsd-m 2.5 --out ./ndvi_salidas

Estadísticas por parcela (Statistical API) + imagen:
  python3 fetch_ndvi_process_api.py ... --index ndvi \\
    --stats-json ./informe_stats.json

Informe mensual viñedo (NDVI+NDRE+NDMI en JSON, imagen NDRE por defecto):
  python3 fetch_ndvi_process_api.py --preset bodegas --informe-mensual \\
    --lon -2.36575 --lat 42.46665 --id parcela1 --radius-m 500 \\
    --from-date 2025-09-01T00:00:00Z --to-date 2025-09-30T23:59:59Z \\
    --stats-json ./informe_bodega.json --gsd-m 2.5 --out ./ndvi_salidas

Solo estadísticas (sin GeoTIFF):
  python3 fetch_ndvi_process_api.py ... --stats-json ./stats.json --no-download

Qué datos y cómo se obtienen (texto detallado):
  python3 fetch_ndvi_process_api.py --info

Flujo informe (catastro, SIGPAC, QGIS, PDF, email):
  python3 fetch_ndvi_process_api.py --pipeline

Polígono SIGPAC / GeoJSON (EPSG:3857 o WGS84):
  python3 fetch_ndvi_process_api.py --geojson parcela.geojson \\
    --from-date 2025-09-01T00:00:00Z --to-date 2025-09-30T23:59:59Z \\
    --preset bodegas --gsd-m 2.5 --out ./ndvi_salidas

NDRE + NDVI en un solo comando (un GeoTIFF por índice):
  python3 fetch_ndvi_process_api.py --geojson parcela.geojson \\
    --index ndre ndvi --from-date ... --to-date ... \\
    --preset bodegas --gsd-m 2.5 --out ./ndvi_salidas
"""
    p = argparse.ArgumentParser(
        description="Sentinel Hub Process + Statistical API (CDSE)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    p.add_argument("--csv", type=Path, help="CSV con columnas id,lon,lat")
    p.add_argument(
        "--geojson",
        type=Path,
        metavar="ARCHIVO",
        help="GeoJSON (FeatureCollection, Feature o Polygon) con el polígono en EPSG:3857 o WGS84; "
        "ignora --lon/--lat/--radius-m para la petición SH.",
    )
    p.add_argument(
        "--geojson-feature-index",
        type=int,
        default=0,
        metavar="N",
        help="Índice del feature si el archivo es FeatureCollection (por defecto 0).",
    )
    p.add_argument(
        "--crs",
        default=None,
        metavar="EPSG",
        help="Forzar CRS si el GeoJSON no declara crs (ej. 3857 o EPSG:3857 para SIGPAC Web Mercator).",
    )
    p.add_argument("--lon", type=float, help="Longitud (si no usas --csv ni --geojson)")
    p.add_argument("--lat", type=float, help="Latitud (si no usas --csv ni --geojson)")
    p.add_argument(
        "--id",
        default="punto",
        help="Identificador de salida si usas --lon/--lat (default: punto)",
    )
    p.add_argument("--radius-m", type=float, default=600.0, help="Radio del bbox en metros")
    p.add_argument(
        "--index",
        dest="indices",
        nargs="+",
        choices=PROCESS_INDEX_CHOICES,
        default=None,
        metavar="INDICE",
        help="Índice(s) de imagen Process API. Puedes pedir varios en un solo comando "
        "(ej. --index ndre ndvi → un archivo por índice). SCL solo con sentinel-2-l2a. "
        "Por defecto: ndvi; con --preset bodegas y sin --index: solo ndre.",
    )
    p.add_argument("--from-date", required=True, help="Inicio rango ISO, ej. 2025-06-01T00:00:00Z")
    p.add_argument("--to-date", required=True, help="Fin rango ISO, ej. 2025-06-30T23:59:59Z")
    p.add_argument(
        "--format",
        choices=("geotiff", "png", "jpeg"),
        default="geotiff",
        help="Formato de imagen (GeoTIFF recomendado para QGIS)",
    )
    p.add_argument(
        "--style",
        choices=("rgb", "raw"),
        default="rgb",
        help="rgb=NDVI coloreado 3 bandas; raw=NDVI float32 1 banda",
    )
    p.add_argument(
        "--gsd-m",
        type=float,
        default=None,
        metavar="M",
        help="Metros aproximados por píxel en suelo (p. ej. 10≈nativo S2; 2–3 más nítido como en browser). "
        "Si se indica, ignora --width/--height.",
    )
    p.add_argument(
        "--max-side",
        type=int,
        default=4096,
        help="Máximo de píxeles por lado al usar --gsd-m (evita peticiones enormes).",
    )
    p.add_argument(
        "--width",
        type=int,
        default=2048,
        help="Ancho en píxeles (si no usas --gsd-m). Por defecto 2048 para más nitidez que 1024.",
    )
    p.add_argument(
        "--height",
        type=int,
        default=2048,
        help="Alto en píxeles (si no usas --gsd-m).",
    )
    p.add_argument("--out", type=Path, default=Path("ndvi_salidas"))
    p.add_argument(
        "--legend-png",
        action="store_true",
        help="Tras la descarga, crea un PNG con la imagen y leyenda de color (índices NDVI/NDRE/NDMI/NDWI con --style rgb).",
    )
    p.add_argument(
        "--collection",
        default="sentinel-2-l1c",
        metavar="TIPO",
        help="Colección S2: sentinel-2-l1c (por defecto) o sentinel-2-l2a (corrección atmosférica L2A).",
    )
    p.add_argument(
        "--resampling",
        choices=("smooth", "nearest"),
        default="smooth",
        help="smooth=BICUBIC/BILINEAR (menos bloques al ampliar; parecido al browser). nearest=sin suavizar.",
    )
    p.add_argument(
        "--max-cloud",
        type=int,
        default=90,
        metavar="PCT",
        help="Máx. nubes 0-99 (dataFilter). 100 = desactivar filtro.",
    )
    p.add_argument(
        "--mosaicking-order",
        choices=("leastCC", "mostRecent", "leastRecent"),
        default="leastCC",
        help="Orden de escenas (leastCC suele coincidir mejor con el browser).",
    )
    p.add_argument(
        "--preset",
        choices=("bodegas",),
        default=None,
        help="Viñedo: por defecto L2A, NDRE en imagen y P10D en stats (solo si no pasas --collection/--index/--stats-interval).",
    )
    p.add_argument(
        "--informe-mensual",
        action="store_true",
        help="Con --stats-json, guarda estadísticas de NDVI, NDRE y NDMI por cliente (JSON anidado por índice).",
    )
    p.add_argument(
        "--stats-json",
        type=Path,
        default=None,
        metavar="ARCHIVO",
        help="Ruta JSON: estadísticas (mean, min, max, percentiles) vía Statistical API por cliente.",
    )
    p.add_argument(
        "--stats-interval",
        default="P10D",
        metavar="ISO8601_DUR",
        help="Agregación temporal Statistical API (ej. P1D, P10D, P1M). "
        "P1M: usar --to-date al inicio del mes siguiente (p. ej. sept.→2025-10-01T00:00:00Z); "
        "si no, la API puede devolver data vacía. Por defecto P10D.",
    )
    p.add_argument(
        "--no-download",
        action="store_true",
        help="No descargar imagen (solo útil con --stats-json).",
    )
    p.add_argument(
        "--clip-to-geometry",
        action="store_true",
        help="Si usas --geojson y --format geotiff, recorta al polígono y crea alpha fuera de parcela.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo imprime el payload JSON del primer cliente y sale",
    )
    ns = p.parse_args(argv)
    if ns.geojson is not None:
        if ns.csv is not None:
            p.error("No combines --geojson con --csv")
        if ns.lon is not None or ns.lat is not None:
            p.error("No combines --geojson con --lon/--lat")
    elif ns.csv is not None:
        if ns.lon is not None or ns.lat is not None:
            p.error("No combines --csv con --lon/--lat")
    else:
        if ns.lon is None or ns.lat is None:
            p.error("Indica --csv, --geojson o bien --lon y --lat juntos")
    if ns.max_side < 64:
        p.error("--max-side debe ser >= 64")
    if not 0 <= ns.max_cloud <= 100:
        p.error("--max-cloud debe estar entre 0 y 100")
    if ns.no_download and ns.stats_json is None:
        p.error("--no-download requiere --stats-json")
    if ns.informe_mensual and ns.stats_json is None:
        p.error("--informe-mensual requiere --stats-json")
    if ns.clip_to_geometry and ns.geojson is None:
        p.error("--clip-to-geometry requiere --geojson")
    if ns.clip_to_geometry and ns.format != "geotiff":
        p.error("--clip-to-geometry requiere --format geotiff")
    return ns


def apply_bodegas_preset(argv_list: list[str], ns: argparse.Namespace) -> None:
    """Solo aplica si no se pasaron explícitamente los flags mencionados."""
    if ns.preset != "bodegas":
        return
    flags: set[str] = set()
    for a in argv_list:
        if a.startswith("--") and "=" in a:
            flags.add(a.split("=", 1)[0])
        elif a.startswith("--"):
            flags.add(a)
    if "--collection" not in flags:
        ns.collection = "sentinel-2-l2a"
    if "--index" not in flags:
        ns.indices = ["ndre"]
    if "--stats-interval" not in flags:
        ns.stats_interval = "P10D"


def finalize_indices(ns: argparse.Namespace) -> None:
    """Un solo --index por defecto ndvi; sin duplicados conservando orden."""
    if ns.indices is None:
        ns.indices = ["ndvi"]
    seen: set[str] = set()
    out: list[str] = []
    for x in ns.indices:
        if x not in seen:
            seen.add(x)
            out.append(x)
    ns.indices = out


def main(argv: list[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(argv)
    apply_bodegas_preset(argv_list, args)
    finalize_indices(args)
    if (
        args.stats_json is not None
        and not args.informe_mensual
        and len(args.indices) == 1
        and args.indices[0] == "truecolor"
    ):
        print(
            "truecolor no tiene estadísticas útiles en modo índice único; "
            "usa --informe-mensual u otro --index.",
            file=sys.stderr,
        )
        return 1
    if args.style == "raw" and len(args.indices) > 1:
        print(
            "Con --style raw solo se admite un índice: ndvi (p. ej. --index ndvi).",
            file=sys.stderr,
        )
        return 1
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.csv:
        clientes = load_clientes_csv(args.csv)
    elif args.geojson is not None:
        try:
            geom, crs_urn, props = load_geojson_area(
                args.geojson,
                args.geojson_feature_index,
                args.crs,
            )
        except (ValueError, OSError, KeyError) as e:
            print(str(e), file=sys.stderr)
            return 1
        epsg = "3857" if "3857" in crs_urn else "4326"
        lon, lat = centroid_lonlat_from_geometry(geom, epsg)
        cid = resolve_geojson_cliente_id(args, props, argv_list)
        clientes = [
            Cliente(
                cliente_id=cid,
                lon=lon,
                lat=lat,
                geometry=geom,
                crs_urn=crs_urn,
            )
        ]
        print(
            f"GeoJSON: {args.geojson.resolve()} (feature {args.geojson_feature_index}, {crs_urn})",
            file=sys.stderr,
        )
    else:
        clientes = [Cliente(cliente_id=args.id, lon=float(args.lon), lat=float(args.lat))]

    if not clientes:
        print("No hay clientes para procesar.", file=sys.stderr)
        return 1

    if "scl" in args.indices and "l2a" not in args.collection.lower():
        print(
            "El índice SCL solo existe en Sentinel-2 L2A. Usa --collection sentinel-2-l2a.",
            file=sys.stderr,
        )
        return 1

    evalscripts: dict[str, str] = {}
    for ix in args.indices:
        try:
            evalscripts[ix] = get_process_evalscript(ix, args.style)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1

    mime = mime_for_format(args.format)
    dw, dh = raster_size_for_cliente(clientes[0], args)
    max_cloud_arg: int | None = None if args.max_cloud >= 100 else args.max_cloud
    fc0 = clientes[0]
    eval_first = evalscripts[args.indices[0]]
    if fc0.geometry is not None and fc0.crs_urn is not None:
        sample_payload = build_payload_polygon(
            fc0.geometry,
            fc0.crs_urn,
            args.from_date,
            args.to_date,
            dw,
            dh,
            mime,
            eval_first,
            collection=args.collection,
            resampling=args.resampling,
            max_cloud_coverage=max_cloud_arg,
            mosaicking_order=args.mosaicking_order,
        )
    else:
        first_bbox = bbox_around_point(fc0.lon, fc0.lat, args.radius_m)
        sample_payload = build_payload(
            first_bbox,
            args.from_date,
            args.to_date,
            dw,
            dh,
            mime,
            eval_first,
            collection=args.collection,
            resampling=args.resampling,
            max_cloud_coverage=max_cloud_arg,
            mosaicking_order=args.mosaicking_order,
        )
    if args.dry_run:
        print(json.dumps(sample_payload, indent=2, ensure_ascii=False))
        if len(args.indices) > 1:
            rest = ", ".join(args.indices[1:])
            print(
                f"(dry-run muestra el payload del primer índice {args.indices[0]}; "
                f"también se pediría: {rest})",
                file=sys.stderr,
            )
        return 0

    print(
        f"Fuente: Sentinel-2 (colección {args.collection}); "
        f"índice(s) imagen: {', '.join(args.indices)}.",
        file=sys.stderr,
    )
    if args.preset == "bodegas":
        print(
            "Preset bodegas: L2A + NDRE por defecto; informe mensual con "
            "--informe-mensual + --stats-json (NDVI+NDRE+NDMI).",
            file=sys.stderr,
        )
    if args.informe_mensual:
        print(
            f"Informe mensual: estadísticas {', '.join(INFORME_INDICES_ESTADISTICAS)} por parcela.",
            file=sys.stderr,
        )
    rs = "BICUBIC/BILINEAR" if args.resampling == "smooth" else "NEAREST"
    print(
        f"Remuestreo: {rs}; mosaico: {args.mosaicking_order}; nubes≤{args.max_cloud if args.max_cloud < 100 else 'sin filtro'}%.",
        file=sys.stderr,
    )
    oauth = create_oauth_session()
    stats_bundle: dict[str, dict] = {}
    for c in clientes:
        w, h = raster_size_for_cliente(c, args)
        if not args.no_download:
            if args.gsd_m is not None:
                print(
                    f"{c.cliente_id}: imagen {w}×{h} px (~{args.gsd_m} m/px, techo {args.max_side}).",
                    file=sys.stderr,
                )
            else:
                print(f"{c.cliente_id}: imagen {w}×{h} px.", file=sys.stderr)

        if args.stats_json is not None:
            if args.informe_mensual:
                por_indice: dict[str, dict] = {}
                for ix in INFORME_INDICES_ESTADISTICAS:
                    por_indice[ix] = post_stats_for_index(
                        oauth, c, args, max_cloud_arg, ix
                    )
                    print(f"OK stats {c.cliente_id} :: {ix}", file=sys.stderr)
                stats_bundle[c.cliente_id] = por_indice
            else:
                stats_bundle[c.cliente_id] = post_stats_for_index(
                    oauth, c, args, max_cloud_arg, args.indices[0]
                )
                print(f"OK stats {c.cliente_id}", file=sys.stderr)

        if not args.no_download:
            for ix in args.indices:
                es = evalscripts[ix]
                path = fetch_for_cliente(
                    oauth,
                    c,
                    radius_m=args.radius_m,
                    time_from=args.from_date,
                    time_to=args.to_date,
                    width=w,
                    height=h,
                    out_format=args.format,
                    out_dir=out_dir,
                    collection=args.collection,
                    index=ix,
                    evalscript=es,
                    resampling=args.resampling,
                    max_cloud_coverage=max_cloud_arg,
                    mosaicking_order=args.mosaicking_order,
                )
                if args.clip_to_geometry and c.geometry is not None and c.crs_urn is not None:
                    try:
                        clip_raster_to_geometry(path, c.geometry, c.crs_urn)
                    except Exception as e:
                        print(
                            f"Aviso: no se pudo recortar al polígono ({path.name}): {e}",
                            file=sys.stderr,
                        )
                print(f"OK {c.cliente_id} -> {path}")
                if args.legend_png:
                    try:
                        leg = write_rgb_preview_with_legend(
                            path, ix, style=args.style
                        )
                        if leg is not None:
                            print(f"     leyenda -> {leg}", file=sys.stderr)
                        else:
                            print(
                                "     (sin leyenda: usa --style rgb y un índice "
                                "ndvi/ndre/ndmi/ndwi, o la salida no es RGB)",
                                file=sys.stderr,
                            )
                    except RuntimeError as e:
                        print(str(e), file=sys.stderr)
                        return 1
                    except Exception as e:
                        print(f"Aviso: no se pudo crear la leyenda: {e}", file=sys.stderr)

    if args.stats_json is not None:
        out_obj: dict = {
            "preset": args.preset,
            "informe_mensual": bool(args.informe_mensual),
            "collection": args.collection,
            "indices": list(args.indices),
            "index": args.indices[0],
            "stats_interval": args.stats_interval,
            "from_date": args.from_date,
            "to_date": args.to_date,
            "clients": stats_bundle,
        }
        if args.geojson is not None:
            out_obj["geojson"] = str(args.geojson.resolve())
        if args.informe_mensual:
            out_obj["indices_estadisticas"] = list(INFORME_INDICES_ESTADISTICAS)
        args.stats_json.write_text(
            json.dumps(out_obj, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Estadísticas guardadas en {args.stats_json.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    if "--info" in sys.argv:
        print(DATA_MODEL_INFO)
        raise SystemExit(0)
    if "--pipeline" in sys.argv:
        print(PIPELINE_BODEGAS_INFO)
        raise SystemExit(0)
    raise SystemExit(main())
