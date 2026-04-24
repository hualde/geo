import os
import json
import subprocess
import math
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from dotenv import load_dotenv
from openai import OpenAI

# Configuración de rutas
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = PROJECT_ROOT / "geojson_entrada"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"
ASSETS_DIR = PROJECT_ROOT / "assets"
ENV_FILE = SRC_DIR / ".env"
load_dotenv(ENV_FILE)


def log_step(message):
    """Log de progreso visible en terminal."""
    print(f"[report] {message}", flush=True)


def parse_parcel_names_from_env():
    """
    Lee nombres de parcelas desde REPORT_PARCEL_NAMES.
    Formato: "Parcela Norte,Parcela Sur,Parcela Este"
    """
    raw = os.environ.get("REPORT_PARCEL_NAMES", "").strip()
    if not raw:
        return []
    return [name.strip() for name in raw.split(",") if name.strip()]


def parse_grape_varieties_from_env():
    """
    Lee variedades desde REPORT_GRAPE_VARIETIES.
    Formato: "Tempranillo,Garnacha,Albillo"
    """
    raw = os.environ.get("REPORT_GRAPE_VARIETIES", "").strip()
    if not raw:
        return []
    return [name.strip() for name in raw.split(",") if name.strip()]

# Buscamos el primer geojson en la carpeta de entrada, si no existe usamos el demo
geojson_files = list(INPUT_DIR.glob("*.geojson"))
GEOJSON_FILE = geojson_files[0] if geojson_files else DATA_DIR / "parcela_demo.geojson"
print(f"--- Usando archivo de entrada: {GEOJSON_FILE.name} ---")

# URLs de servicios WMS (España)
WMS_PNOA = "https://www.ign.es/wms-inspire/pnoa-ma"
WMS_CATASTRO = "https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx"
WMS_TOPO = "https://www.ign.es/wms-inspire/ign-base"
WMS_MDT = "https://www.ign.es/wms-inspire/mdt" # Para pendientes y relieve

def get_wms_image(bbox, layer, service_url, filename, crs="EPSG:4326", width=1800, height=1200, output_dir=None):
    """Descarga una imagen de un servicio WMS con reintentos para mayor robustez."""
    import time
    target_dir = output_dir if output_dir else WMS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / filename
    
    # En WMS 1.3.0 y EPSG:4326, el orden es Latitud, Longitud (Y, X)
    bbox_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
    
    params = {
        "service": "WMS",
        "version": "1.1.1", # Cambiamos a 1.1.1 para mayor compatibilidad
        "request": "GetMap",
        "layers": layer,
        "styles": "",
        "srs": crs,
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}", # Lon, Lat (Orden estándar 1.1.1)
        "width": width,
        "height": height,
        "format": "image/png",
        "transparent": "TRUE"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(service_url, params=params, timeout=45)
            if response.status_code == 200:
                # Verificamos que no sea un XML de error disfrazado de PNG
                content_start = response.content[:500]
                if b"ServiceException" in content_start or b"<?xml" in content_start:
                    print(f"!!! Error WMS en {layer} (intento {attempt+1}): Respuesta no es imagen")
                    # Si falla en 1.1.1, probamos 1.3.0 con cambio de ejes como último recurso
                    if attempt == 0:
                        params["version"] = "1.3.0"
                        params["crs"] = crs
                        del params["srs"]
                        params["bbox"] = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
                else:
                    with open(out_path, "wb") as f:
                        f.write(response.content)
                    return out_path
            
            print(f"!!! Intento {attempt+1} fallido WMS {layer}: {response.status_code}")
            if response.status_code in [502, 503, 504]:
                time.sleep(2 * (attempt + 1)) # Espera progresiva
            else:
                break # Si es error 404 o similar, no reintentar
        except Exception as e:
            print(f"Error en intento {attempt+1} WMS ({layer}): {e}")
            time.sleep(2)
            
    return None

def calculate_surface(geometry):
    """Calcula la superficie aproximada en hectáreas."""
    coords = geometry['coordinates'][0]
    area = 0.0
    for i in range(len(coords)):
        j = (i + 1) % len(coords)
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    area = abs(area) / 2.0
    m2 = area * 111320 * 82600 
    return round(m2 / 10000, 2)

def run_sentinel_api(feature_index, parcel_id, from_date, to_date):
    """Llamada al motor geoespacial."""
    RASTER_DIR.mkdir(parents=True, exist_ok=True)
    stats_file = RASTER_DIR / f"stats_{parcel_id}.json"
    cmd = [
        "python3", str(SRC_DIR / "fetch_ndvi_process_api.py"),
        "--geojson", str(GEOJSON_FILE),
        "--geojson-feature-index", str(feature_index),
        "--id", parcel_id,
        "--preset", "bodegas",
        "--informe-mensual",
        "--stats-json", str(stats_file),
        "--from-date", from_date,
        "--to-date", to_date,
        "--out", str(RASTER_DIR),
        "--format", "png",
        "--style", "rgb"
    ]
    subprocess.run(cmd, capture_output=True)
    return stats_file

def overlay_geometry(image_path, geometry, bbox, output_path):
    """Dibuja la linde de la parcela sobre una imagen existente."""
    if not image_path or not os.path.exists(image_path): return None
    
    import matplotlib.image as mpimg
    img = mpimg.imread(image_path)
    
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    # Mostramos la imagen ajustada al BBOX
    ax.imshow(img, extent=[bbox[0], bbox[2], bbox[1], bbox[3]])
    
    # Dibujamos la linde (Burdeos ATLAS con borde blanco para contraste)
    from shapely.geometry import shape
    if hasattr(geometry, '__geo_interface__'):
        poly = geometry
    else:
        poly = shape(geometry)
        
    line_color = '#6B1D23' # Burdeos ATLAS (Granate oscuro)
    if poly.geom_type == 'Polygon':
        x, y = poly.exterior.xy
        ax.plot(x, y, color='white', linewidth=8.0, alpha=0.4) # Halo para contraste
        ax.plot(x, y, color=line_color, linewidth=6.0)
    elif poly.geom_type == 'MultiPolygon':
        for part in poly.geoms:
            x, y = part.exterior.xy
            ax.plot(x, y, color='white', linewidth=8.0, alpha=0.4)
            ax.plot(x, y, color=line_color, linewidth=6.0)

    ax.set_axis_off()
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0,0)
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
    plt.close()
    return output_path

def generate_multi_index_chart(stats_file, parcel_id, output_dir):
    """Genera gráfica con la paleta de colores ATLAS."""
    with open(stats_file, 'r') as f:
        stats_data = json.load(f)
    
    client_stats = stats_data['clients'][parcel_id]
    plt.figure(figsize=(10, 5), dpi=100)
    
    # Paleta ATLAS
    colors = {'ndvi': '#4a5a2a', 'ndre': '#a8772a', 'ndmi': '#6a1f1f', 'chl': '#2f7d32'}
    paper_color = '#ece3d0'
    ink_color = '#1f1e16'
    month_abbr_es = {
        1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
        7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
    }

    def format_month_es(x, _):
        dt = mdates.num2date(x)
        return f"{month_abbr_es.get(dt.month, '')}-{str(dt.year)[-2:]}"

    ax = plt.gca()
    ax2 = ax.twinx()
    ax.set_facecolor(paper_color)
    plt.gcf().set_facecolor(paper_color)

    left_lines = []
    right_lines = []
    for idx in ['ndvi', 'ndre', 'ndmi', 'chl']:
        if idx not in client_stats:
            continue
        data = client_stats[idx]['data']
        dates = [datetime.strptime(e['interval']['from'][:10], '%Y-%m-%d') for e in data if 'outputs' in e]
        values = [e['outputs']['index']['bands']['B0']['stats']['mean'] for e in data if 'outputs' in e]
        if not values:
            continue

        label = "CIg" if idx == "chl" else idx.upper()
        target_ax = ax2 if idx == "chl" else ax
        line = target_ax.plot(
            dates,
            values,
            label=label,
            color=colors[idx],
            linewidth=2.5,
            marker='o',
            markersize=4,
        )[0]
        if idx == "chl":
            right_lines.append(line)
        else:
            left_lines.append(line)

    plt.title(f"EVOLUCIÓN CARTOGRÁFICA — {parcel_id}", fontsize=12, color=ink_color, pad=20, fontfamily='serif')
    ax.grid(True, linestyle='--', alpha=0.3, color=ink_color)
    ax.xaxis.set_major_formatter(FuncFormatter(format_month_es))
    ax.set_ylabel("")
    ax2.set_ylabel("CIg (Clorofila)", color=colors['chl'], fontsize=9)
    ax2.tick_params(axis='y', colors=colors['chl'])

    all_lines = left_lines + right_lines
    if all_lines:
        all_labels = [line.get_label() for line in all_lines]
        ax.legend(all_lines, all_labels, frameon=False, fontsize='small', loc='upper left')
    
    # Eliminar bordes innecesarios
    for spine in ax.spines.values():
        spine.set_color(ink_color)
        spine.set_alpha(0.2)
    for spine in ax2.spines.values():
        spine.set_color(ink_color)
        spine.set_alpha(0.2)
        
    plt.tight_layout()
    chart_path = output_dir / f"evolucion_{parcel_id}.png"
    plt.savefig(chart_path, facecolor=paper_color)
    plt.close()
    return chart_path


def monthly_window_last_year():
    """
    Devuelve (from_date, to_date) para cubrir los 12 meses completos anteriores.
    Ejemplo: si hoy es 2026-04-23 -> [2025-04-01, 2026-04-01).
    """
    today = datetime.utcnow()
    current_month_start = datetime(today.year, today.month, 1)
    start_year = current_month_start.year - 1
    start_month = current_month_start.month
    from_date = datetime(start_year, start_month, 1).strftime("%Y-%m-%dT00:00:00Z")
    to_date = current_month_start.strftime("%Y-%m-%dT00:00:00Z")
    return from_date, to_date


def extract_full_stats(stats_file, parcel_id):
    """Extrae todas las estadísticas por índice e intervalo para el reporte JSON."""
    indices = ["ndvi", "ndre", "ndmi", "chl"]
    full_stats = {ix: {"series": []} for ix in indices}

    if not stats_file.exists():
        return full_stats

    try:
        with open(stats_file, "r") as f:
            sd = json.load(f)

        client_data = sd.get("clients", {}).get(parcel_id, {})
        for ix in indices:
            ix_data = client_data.get(ix, {})
            intervals = ix_data.get("data", [])
            for entry in intervals:
                if "outputs" not in entry:
                    continue
                stats = (
                    entry.get("outputs", {})
                    .get("index", {})
                    .get("bands", {})
                    .get("B0", {})
                    .get("stats", {})
                )
                if not stats:
                    continue

                full_stats[ix]["series"].append(
                    {
                        "interval": entry.get("interval", {}),
                        "stats": {
                            "min": stats.get("min"),
                            "max": stats.get("max"),
                            "mean": stats.get("mean"),
                            "stDev": stats.get("stDev"),
                            "sampleCount": stats.get("sampleCount"),
                            "noDataCount": stats.get("noDataCount"),
                            "percentiles": stats.get("percentiles", {}),
                        },
                    }
                )
    except Exception:
        return full_stats

    return full_stats


def build_monthly_real_data(full_stats):
    """Normaliza los datos por mes para consumo directo en el JSON final."""
    monthly = {}
    for ix, ix_payload in full_stats.items():
        series = ix_payload.get("series", [])
        ix_months = []
        for entry in series:
            interval = entry.get("interval", {})
            stats = entry.get("stats", {})
            from_date = interval.get("from", "")
            month_key = from_date[:7] if from_date else ""
            ix_months.append(
                {
                    "mes": month_key,
                    "from": interval.get("from"),
                    "to": interval.get("to"),
                    "mean": stats.get("mean"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "stDev": stats.get("stDev"),
                    "sampleCount": stats.get("sampleCount"),
                    "noDataCount": stats.get("noDataCount"),
                    "percentiles": stats.get("percentiles", {}),
                }
            )
        monthly[ix] = ix_months
    return monthly


def build_ai_dataset(parcels_json, report_from_date, report_to_date):
    """Prepara un dataset compacto (pero completo) para el análisis de IA."""
    ai_parcels = []
    for p in parcels_json:
        monthly = p.get("datos_reales_ultimo_anio_mensual", {})
        compact_monthly = {}
        for ix, rows in monthly.items():
            compact_monthly[ix] = [
                {
                    "mes": r.get("mes"),
                    "mean": r.get("mean"),
                    "min": r.get("min"),
                    "max": r.get("max"),
                    "stDev": r.get("stDev"),
                }
                for r in rows
            ]
        ai_parcels.append(
            {
                "id": p.get("id"),
                "nombre": p.get("nombre"),
                "info": p.get("info", {}),
                "fisiografia": p.get("fisiografia", {}),
                "datos_reales_ultimo_anio_mensual": compact_monthly,
                "summary_for_pdf": p.get("summary_for_pdf", {}),
            }
        )
    return {
        "periodo": {
            "from_date": report_from_date,
            "to_date": report_to_date,
            "stats_interval": "P1M",
        },
        "parcels": ai_parcels,
    }


def enrich_with_openai_analysis(parcels_data, ai_dataset):
    """
    Completa dictamen/tendencia/recomendacion usando OpenAI.
    Si falta credencial o falla la API, mantiene los valores existentes.
    """
    api_key = (
        os.environ.get("DEEPSEEK_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )
    ai_enabled = os.environ.get("OPENAI_ENABLE", "true").strip().lower() in ("1", "true", "yes", "y")
    if not ai_enabled:
        log_step("OPENAI_ENABLE=false; se omite análisis IA.")
        return None
    if not api_key:
        log_step("OPENAI_API_KEY no definida; se usan textos locales por defecto.")
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    connect_timeout = float(os.environ.get("OPENAI_CONNECT_TIMEOUT", "10"))
    read_timeout = float(os.environ.get("OPENAI_READ_TIMEOUT", "35"))
    thinking_enabled = os.environ.get("OPENAI_THINKING", "false").strip().lower() in ("1", "true", "yes", "y")
    prompt = (
        "Eres un enólogo y viticultor especializado en viticultura de precisión con amplia experiencia "
        "en Denominaciones de Origen españolas. Voy a proporcionarte datos de teledetección satelital "
        "(Sentinel-2) de varias parcelas de viñedo.\n"
        "Los índices que encontrarás en los datos son:\n\n"
        "NDVI: vigor vegetativo general\n"
        "NDRE: estado nutricional y clorofila en capas profundas del dosel\n"
        "NDMI: estado hídrico de la vegetación\n"
        "CHL: contenido de clorofila foliar, proxy del estado nitrogenado\n\n"
        "El mes actual es el último mes del período analizado en los datos. Ten esto en cuenta para "
        "contextualizar el momento del ciclo en que nos encontramos ahora mismo y orientar las "
        "recomendaciones a acciones que se pueden tomar de forma inmediata.\n"
        "Cuando recibas los datos, analiza cada parcela y el conjunto, y devuelve un informe estructurado "
        "con los siguientes apartados:\n"
        "1. Diagnóstico fenológico\n"
        "2. Comparativa de vigor entre parcelas\n"
        "3. Estado nutricional (NDRE y CHL)\n"
        "4. Estado hídrico (NDMI)\n"
        "5. Riesgos agronómicos detectados\n"
        "6. Recomendaciones de manejo de precisión\n"
        "7. Perspectiva de calidad para la cosecha\n\n"
        "Sé técnico y específico con los valores numéricos de los datos. Cuando detectes algo llamativo "
        "o inusual, señálalo explícitamente. Evita generalidades que no estén respaldadas por los datos adjuntos.\n\n"
        "Devuelve SIEMPRE JSON válido con esta estructura exacta:\n"
        "{\n"
        "  \"analisis_global\": {\n"
        "    \"diagnostico_fenologico\": \"texto\",\n"
        "    \"comparativa_vigor\": \"texto\",\n"
        "    \"estado_nutricional\": \"texto\",\n"
        "    \"estado_hidrico\": \"texto\",\n"
        "    \"riesgos_agronomicos\": \"texto\",\n"
        "    \"recomendaciones_manejo\": \"texto\",\n"
        "    \"perspectiva_calidad\": \"texto\"\n"
        "  },\n"
        "  \"parcelas\": {\n"
        "    \"<ID_PARCELA>\": {\n"
        "      \"dictamen\": \"texto corto\",\n"
        "      \"tendencia\": \"texto corto\",\n"
        "      \"recomendacion\": \"texto de 2-4 frases\",\n"
        "      \"diagnostico_fenologico\": \"texto\",\n"
        "      \"estado_nutricional\": \"texto\",\n"
        "      \"estado_hidrico\": \"texto\",\n"
        "      \"riesgos\": [\"riesgo1\", \"riesgo2\"]\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        "Los datos son los siguientes:\n"
        f"{json.dumps(ai_dataset, ensure_ascii=False)}"
    )

    try:
        log_step(f"Solicitando análisis IA a {base_url} con modelo {model}...")
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=read_timeout,
            max_retries=2,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Eres un agrónomo experto en viticultura de precisión."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            stream=False,
            extra_body={"thinking": {"type": "enabled" if thinking_enabled else "disabled"}},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        log_step("Análisis IA recibido correctamente.")
    except Exception as e:
        log_step(f"No se pudo obtener análisis IA ({e}). Se mantienen textos locales.")
        return None

    by_parcel = parsed.get("parcelas", {})
    for parcel in parcels_data:
        parcel_id = parcel.get("id")
        ai_p = by_parcel.get(parcel_id, {})
        if ai_p:
            parcel["dictamen"] = ai_p.get("dictamen", parcel.get("dictamen", "N/D"))
            parcel["tendencia"] = ai_p.get("tendencia", parcel.get("tendencia", "N/D"))
            parcel["recomendacion"] = ai_p.get("recomendacion", parcel.get("recomendacion", "N/D"))

    return parsed

def main():
    if not GEOJSON_FILE.exists(): return
    log_step(f"Iniciando generación de informe para {GEOJSON_FILE.name}")

    import geopandas as gpd
    gdf = gpd.read_file(GEOJSON_FILE)
    
    # Identificamos el mes actual para la carpeta de entrega
    mes_actual = datetime.now().strftime("%Y_%m")
    
    report_from_date, report_to_date = monthly_window_last_year()
    cover_brand = os.environ.get("REPORT_COVER_BRAND", "Bodega Ejemplo").strip() or "Bodega Ejemplo"
    env_parcel_names = parse_parcel_names_from_env()
    env_grape_varieties = parse_grape_varieties_from_env()
    default_grape_variety = os.environ.get("REPORT_DEFAULT_GRAPE_VARIETY", "Tinta del País").strip() or "Tinta del País"
    parts = cover_brand.split(maxsplit=1)
    cover_brand_primary = parts[0]
    cover_brand_secondary = parts[1] if len(parts) > 1 else ""
    parcels_data = []
    json_parcels = []
    for i, (idx, feat) in enumerate(gdf.iterrows()):
        p_id = str(feat.get('id', f"P{i}"))
        p_nombre = str(feat.get('nombre', p_id))
        if i < len(env_parcel_names):
            p_nombre = env_parcel_names[i]
        # Si no hay nombre explícito y el ID es P<n>, mostrar "Parcela n"
        if p_nombre == p_id and re.fullmatch(r"P\d+", p_id):
            p_nombre = f"Parcela {p_id[1:]}"
        p_variedad = str(feat.get("variedad", default_grape_variety))
        if i < len(env_grape_varieties):
            p_variedad = env_grape_varieties[i]
        props = feat.to_dict() # Para compatibilidad con el resto del script
        
        # Nueva estructura de carpetas: assets/entregas/ID_CLIENTE/2025_04/
        CLIENT_DIR = ASSETS_DIR / "entregas" / p_id / mes_actual
        RASTER_OUT = CLIENT_DIR / "raster"
        WMS_OUT = CLIENT_DIR / "wms"
        CHARTS_OUT = CLIENT_DIR / "charts"
        
        for d in [RASTER_OUT, WMS_OUT, CHARTS_OUT]: d.mkdir(parents=True, exist_ok=True)
        
        parcel = feat['geometry']
        
        # LOCALIZACIÓN (Cálculo de BBOX dinámico con proporción 3:2)
        min_lon, min_lat, max_lon, max_lat = parcel.bounds
        center_lon, center_lat = (min_lon + max_lon) / 2, (min_lat + max_lat) / 2
        width, height = max_lon - min_lon, max_lat - min_lat
        
        # Queremos un ratio de 1.5 (1800/1200)
        target_ratio = 1.5
        current_ratio = width / height if height > 0 else 1
        
        if current_ratio > target_ratio:
            view_w = width * 1.5 
            view_h = view_w / target_ratio
        else:
            view_h = height * 1.5
            view_w = view_h * target_ratio
            
        bbox_mid = [center_lon - view_w/2, center_lat - view_h/2, center_lon + view_w/2, center_lat + view_h/2]
        
        # Para el topo, alejamos la vista 6 veces
        view_w_wide, view_h_wide = view_w * 6, view_h * 6
        bbox_wide = [center_lon - view_w_wide/2, center_lat - view_h_wide/2, center_lon + view_w_wide/2, center_lat + view_h_wide/2]
        
        # Descarga
        log_step(f"[{p_id}] Descargando cartografía base WMS...")
        img_pnoa = get_wms_image(bbox_mid, "OI.OrthoimageCoverage", WMS_PNOA, f"pnoa_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        img_topo = get_wms_image(bbox_wide, "IGNBaseTodo", WMS_TOPO, f"topo_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        
        # Foto de límites (Overlay)
        path_overlay = WMS_OUT / f"overlay_{p_id}_{mes_actual}.png"
        img_sigpac = overlay_geometry(img_pnoa, parcel, bbox_mid, path_overlay)
        
        # SATÉLITE
        log_step(f"[{p_id}] Solicitando índices y estadísticas Sentinel...")
        stats_file = RASTER_OUT / f"stats_{p_id}_{mes_actual}.json"
        cmd = [
            "python3", str(SRC_DIR / "fetch_ndvi_process_api.py"),
            "--geojson", str(GEOJSON_FILE),
            "--geojson-feature-index", str(i),
            "--id", p_id,
            "--preset", "bodegas",
            "--index", "ndvi", "ndre", "ndmi", "chl",
            "--informe-mensual",
            "--stats-interval", "P1M",
            "--stats-json", str(stats_file),
            "--from-date", report_from_date,
            "--to-date", report_to_date,
            "--out", str(RASTER_OUT),
            "--format", "png",
            "--style", "rgb"
        ]
        try:
            sentinel_run = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if sentinel_run.returncode != 0:
                log_step(f"[{p_id}] Sentinel devolvió código {sentinel_run.returncode}.")
        except subprocess.TimeoutExpired:
            log_step(f"[{p_id}] Timeout en Sentinel (>300s). Se continúa con datos disponibles.")
        
        log_step(f"[{p_id}] Generando gráfica temporal...")
        chart_path = generate_multi_index_chart(stats_file, p_id, CHARTS_OUT)

        # FUNCIÓN AUXILIAR PARA RESOLVER RUTAS
        def resolve_img(prop_key, default_file):
            custom_path = feat.get(prop_key)
            if custom_path and isinstance(custom_path, str) and os.path.exists(custom_path):
                return f"file://{os.path.abspath(custom_path)}"
            return f"file://{default_file.absolute()}" if default_file and default_file.exists() else ""

        centroid = parcel.centroid
        
        # Cálculo de superficie preciso proyectando a metros
        parcel_meters = gdf.loc[[idx]].to_crs(epsg=3857).geometry.iloc[0]
        superficie_ha = round(parcel_meters.area / 10000, 2)
        
        # Extraemos estadísticas detalladas para la tabla por índice
        stats_summary = {}
        full_stats = {}
        try:
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    sd = json.load(f)
                    for ix in ["ndvi", "ndre", "ndmi", "chl"]:
                        stats_summary[ix] = {"mean": "N/D", "min": "N/D", "max": "N/D"}
                        if ix in sd['clients'][p_id]:
                            intervals = sd['clients'][p_id][ix]['data']
                            valid = [e for e in intervals if 'outputs' in e]
                            if valid:
                                s = valid[-1]['outputs']['index']['bands']['B0']['stats']
                                stats_summary[ix] = {
                                    "mean": round(s['mean'], 3),
                                    "min": round(s['min'], 3),
                                    "max": round(s['max'], 3)
                                }
        except: pass
        full_stats = extract_full_stats(stats_file, p_id)
        monthly_real_data = build_monthly_real_data(full_stats)

        parcels_data.append({
            "id": p_id,
            "id_display": p_nombre,
            "stats": stats_summary,
            "info": {
                "nombre": p_nombre,
                "vina": p_nombre,
                "variedad": p_variedad,
                "lat": round(centroid.y, 6),
                "lon": round(centroid.x, 6)
            },
            "fisiografia": {
                "altitud": "450m",
                "pendiente_pct": "3.2%",
                "superficie": f"{superficie_ha} ha"
            },
            "wms": {
                "pnoa": f"file://{img_pnoa.absolute()}" if img_pnoa else "",
                "sigpac": f"file://{img_sigpac.absolute()}" if img_sigpac else "",
                "topo": f"file://{img_topo.absolute()}" if img_topo else ""
            },
            "indices": {
                "ndvi": resolve_img("path_ndvi", RASTER_OUT / f"{p_id}_ndvi.png"),
                "ndre": resolve_img("path_ndre", RASTER_OUT / f"{p_id}_ndre.png"),
                "ndmi": resolve_img("path_ndmi", RASTER_OUT / f"{p_id}_ndmi.png"),
                "clorofila": resolve_img("path_chl", RASTER_OUT / f"{p_id}_chl.png")
            },
            "chart": f"file://{chart_path.absolute()}",
            "dictamen": "Óptimo", "tendencia": "Estable",
            "recomendacion": "Estado vegetativo excelente. Se recomienda mantener monitorización.",
            "proxima_imagen": (datetime.now() + timedelta(days=3)).strftime("%d/%m/%Y")
        })

        json_parcels.append({
            "id": p_id,
            "nombre": p_nombre,
            "info": {
                "vina": p_nombre,
                "variedad": p_variedad,
                "lat": round(centroid.y, 6),
                "lon": round(centroid.x, 6),
            },
            "fisiografia": {
                "altitud": "450m",
                "pendiente_pct": "3.2%",
                "superficie_ha": superficie_ha,
            },
            "periodo": {
                "from_date": report_from_date,
                "to_date": report_to_date,
            },
            "indices": full_stats,
            "datos_reales_ultimo_anio_mensual": monthly_real_data,
            "assets": {
                "wms": {
                    "pnoa": str(img_pnoa.absolute()) if img_pnoa else "",
                    "sigpac": str(img_sigpac.absolute()) if img_sigpac else "",
                    "topo": str(img_topo.absolute()) if img_topo else "",
                },
                "raster": {
                    "ndvi": str((RASTER_OUT / f"{p_id}_ndvi.png").absolute()),
                    "ndre": str((RASTER_OUT / f"{p_id}_ndre.png").absolute()),
                    "ndmi": str((RASTER_OUT / f"{p_id}_ndmi.png").absolute()),
                    "chl": str((RASTER_OUT / f"{p_id}_chl.png").absolute()),
                },
                "chart": str(chart_path.absolute()),
                "stats_file": str(stats_file.absolute()),
            },
            "summary_for_pdf": stats_summary,
        })

    ai_dataset = build_ai_dataset(json_parcels, report_from_date, report_to_date)
    log_step("Preparando análisis IA de sección 4...")
    ai_analysis = enrich_with_openai_analysis(parcels_data, ai_dataset)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report_template.html")
    html_out = template.render(
        parcels=parcels_data,
        hoy=datetime.now().strftime("%d/%m/%Y"),
        cover_brand=cover_brand,
        cover_brand_primary=cover_brand_primary,
        cover_brand_secondary=cover_brand_secondary,
    )
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # PDF y JSON comparten exactamente el mismo nombre base
    report_name = f"informe_{mes_actual}"
    pdf_path = REPORTS_DIR / f"{report_name}.pdf"
    log_step(f"Renderizando PDF: {pdf_path.name}")
    HTML(string=html_out, base_url=str(PROJECT_ROOT)).write_pdf(pdf_path)
    json_report_path = REPORTS_DIR / f"{report_name}.json"
    json_report = {
        "report_id": report_name,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "satellite": "Sentinel-2",
            "indices": ["ndvi", "ndre", "ndmi", "chl"],
            "stats_provider": "Sentinel Hub Statistical API",
            "raster_provider": "Sentinel Hub Process API",
        },
        "geojson_input": str(GEOJSON_FILE),
        "periodo": {
            "from_date": report_from_date,
            "to_date": report_to_date,
            "stats_interval": "P1M",
        },
        "analisis_ia": ai_analysis if ai_analysis else {},
        "parcels": json_parcels,
    }
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    log_step(f"Informe generado en: {pdf_path}")
    log_step(f"JSON generado en: {json_report_path}")

if __name__ == "__main__":
    main()
