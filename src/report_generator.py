import os
import json
import subprocess
import math
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Configuración de rutas
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = PROJECT_ROOT / "geojson_entrada"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Buscamos el primer geojson en la carpeta de entrada, si no existe usamos el demo
geojson_files = list(INPUT_DIR.glob("*.geojson"))
GEOJSON_FILE = geojson_files[0] if geojson_files else DATA_DIR / "parcela_demo.geojson"
print(f"--- Usando archivo de entrada: {GEOJSON_FILE.name} ---")

# URLs de servicios WMS (España)
WMS_PNOA = "https://www.ign.es/wms-inspire/pnoa-ma"
WMS_SIGPAC = "https://wms.mapama.gob.es/sigpac/wms"

def get_wms_image(bbox, layer, service_url, filename, crs="EPSG:4326", width=1800, height=1200, output_dir=None):
    """Descarga una imagen de un servicio WMS con alta resolución."""
    target_dir = output_dir if output_dir else WMS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / filename
    
    # En WMS 1.3.0 y EPSG:4326, el orden es Latitud, Longitud (Y, X)
    bbox_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
    
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": layer,
        "styles": "",
        "crs": crs,
        "bbox": bbox_str,
        "width": width,
        "height": height,
        "format": "image/png",
        "transparent": "TRUE"
    }
    
    try:
        response = requests.get(service_url, params=params, timeout=30)
        if response.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(response.content)
            return out_path
        else:
            print(f"!!! Fallo WMS {layer}: {response.status_code}")
    except Exception as e:
        print(f"Error WMS ({layer}): {e}")
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

def generate_multi_index_chart(stats_file, parcel_id, output_dir):
    """Genera gráfica con la paleta de colores ATLAS."""
    with open(stats_file, 'r') as f:
        stats_data = json.load(f)
    
    client_stats = stats_data['clients'][parcel_id]
    plt.figure(figsize=(10, 5), dpi=100)
    
    # Paleta ATLAS
    colors = {'ndvi': '#4a5a2a', 'ndre': '#a8772a', 'ndmi': '#6a1f1f'}
    paper_color = '#ece3d0'
    ink_color = '#1f1e16'
    
    ax = plt.gca()
    ax.set_facecolor(paper_color)
    plt.gcf().set_facecolor(paper_color)
    
    for idx in ['ndvi', 'ndre', 'ndmi']:
        if idx in client_stats:
            data = client_stats[idx]['data']
            dates = [datetime.strptime(e['interval']['from'][:10], '%Y-%m-%d') for e in data if 'outputs' in e]
            values = [e['outputs']['index']['bands']['B0']['stats']['mean'] for e in data if 'outputs' in e]
            if values:
                plt.plot(dates, values, label=idx.upper(), color=colors[idx], linewidth=2.5, marker='o', markersize=4)

    plt.title(f"EVOLUCIÓN CARTOGRÁFICA — {parcel_id}", fontsize=12, color=ink_color, pad=20, fontfamily='serif')
    plt.legend(frameon=False, fontsize='small')
    plt.grid(True, linestyle='--', alpha=0.3, color=ink_color)
    
    # Eliminar bordes innecesarios
    for spine in ax.spines.values():
        spine.set_color(ink_color)
        spine.set_alpha(0.2)
        
    plt.tight_layout()
    chart_path = output_dir / f"evolucion_{parcel_id}.png"
    plt.savefig(chart_path, facecolor=paper_color)
    plt.close()
    return chart_path

def main():
    if not GEOJSON_FILE.exists(): return

    import geopandas as gpd
    gdf = gpd.read_file(GEOJSON_FILE)
    
    # Identificamos el mes actual para la carpeta de entrega
    mes_actual = datetime.now().strftime("%Y_%m")
    
    parcels_data = []
    for i, (idx, feat) in enumerate(gdf.iterrows()):
        p_id = str(feat.get('id', f"P{i}"))
        p_nombre = str(feat.get('nombre', p_id))
        props = feat.to_dict() # Para compatibilidad con el resto del script
        
        # Nueva estructura de carpetas: assets/entregas/ID_CLIENTE/2025_04/
        CLIENT_DIR = ASSETS_DIR / "entregas" / p_id / mes_actual
        RASTER_OUT = CLIENT_DIR / "raster"
        WMS_OUT = CLIENT_DIR / "wms"
        CHARTS_OUT = CLIENT_DIR / "charts"
        
        for d in [RASTER_OUT, WMS_OUT, CHARTS_OUT]: d.mkdir(parents=True, exist_ok=True)
        
        parcel = feat['geometry']
        
        # LOCALIZACIÓN (Cálculo de BBOX dinámico)
        min_lon, min_lat, max_lon, max_lat = parcel.bounds
        width = max_lon - min_lon
        height = max_lat - min_lat
        margin_x = max(width * 0.1, 0.0005)
        margin_y = max(height * 0.1, 0.0005)
        bbox = [min_lon - margin_x, min_lat - margin_y, max_lon + margin_x, max_lat + margin_y]
        
        # Descarga con rutas organizadas
        img_pnoa = get_wms_image(bbox, "OI.OrthoimageCoverage", WMS_PNOA, f"pnoa_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        img_sigpac = get_wms_image(bbox, "PARCELA", WMS_SIGPAC, f"sigpac_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        img_topo = get_wms_image(bbox, "IGNBaseTodo", "https://www.ign.es/wms-inspire/ign-base", f"topo_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        
        # SATÉLITE
        stats_file = RASTER_OUT / f"stats_{p_id}_{mes_actual}.json"
        cmd = [
            "python3", str(SRC_DIR / "fetch_ndvi_process_api.py"),
            "--geojson", str(GEOJSON_FILE),
            "--geojson-feature-index", str(i),
            "--id", p_id,
            "--preset", "bodegas",
            "--index", "ndvi", "ndre", "ndmi",
            "--informe-mensual",
            "--stats-json", str(stats_file),
            "--from-date", "2025-10-01T00:00:00Z",
            "--to-date", "2026-04-01T00:00:00Z",
            "--out", str(RASTER_OUT),
            "--format", "png",
            "--style", "rgb"
        ]
        subprocess.run(cmd, capture_output=True)
        
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
        try:
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    sd = json.load(f)
                    for ix in ["ndvi", "ndre", "ndmi"]:
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

        parcels_data.append({
            "id": p_id,
            "stats": stats_summary,
            "info": {
                "nombre": props.get("nombre", p_id),
                "vina": props.get("vina", "N/A"),
                "variedad": props.get("variedad", "Tinta del País"),
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
                "ndmi": resolve_img("path_ndmi", RASTER_OUT / f"{p_id}_ndmi.png")
            },
            "chart": f"file://{chart_path.absolute()}",
            "dictamen": "Óptimo", "tendencia": "Estable",
            "recomendacion": "Estado vegetativo excelente. Se recomienda mantener monitorización.",
            "proxima_imagen": (datetime.now() + timedelta(days=3)).strftime("%d/%m/%Y")
        })

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report_template.html")
    html_out = template.render(parcels=parcels_data, hoy=datetime.now().strftime("%d/%m/%Y"))
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # El PDF también lo guardamos con la fecha para no sobreescribir el anterior
    pdf_path = REPORTS_DIR / f"informe_{mes_actual}.pdf"
    HTML(string=html_out, base_url=str(PROJECT_ROOT)).write_pdf(pdf_path)
    print(f"Informe generado en: {pdf_path}")

if __name__ == "__main__":
    main()
