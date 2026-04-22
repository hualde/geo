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
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"
ASSETS_DIR = PROJECT_ROOT / "assets"
RASTER_DIR = ASSETS_DIR / "raster"
CHARTS_DIR = ASSETS_DIR / "charts"
WMS_DIR = ASSETS_DIR / "wms"

GEOJSON_FILE = DATA_DIR / "parcela_demo.geojson"

# URLs de servicios WMS (España)
WMS_PNOA = "https://www.ign.es/wms-inspire/pnoa-ma"
WMS_SIGPAC = "https://wms.mapama.gob.es/sigpac/wms"

def get_wms_image(bbox, layer, service_url, filename, crs="EPSG:4326", width=1200, height=800):
    """Descarga una imagen de un servicio WMS."""
    WMS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WMS_DIR / filename
    
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

def generate_multi_index_chart(stats_file, parcel_id):
    """Genera gráfica con la paleta de colores ATLAS."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
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
            dates = [datetime.strptime(e['interval']['from'][:10], '%Y-%m-%d') for e in data]
            values = [e['outputs']['index']['bands']['B0']['stats']['mean'] for e in data]
            plt.plot(dates, values, label=idx.upper(), color=colors[idx], linewidth=2.5, marker='o', markersize=4)

    plt.title(f"EVOLUCIÓN CARTOGRÁFICA — {parcel_id}", fontsize=12, color=ink_color, pad=20, fontfamily='serif')
    plt.legend(frameon=False, fontsize='small')
    plt.grid(True, linestyle='--', alpha=0.3, color=ink_color)
    
    # Eliminar bordes innecesarios
    for spine in ax.spines.values():
        spine.set_color(ink_color)
        spine.set_alpha(0.2)
        
    plt.tight_layout()
    chart_path = CHARTS_DIR / f"evolucion_{parcel_id}.png"
    plt.savefig(chart_path, facecolor=paper_color)
    plt.close()
    return chart_path

def main():
    if not GEOJSON_FILE.exists(): return

    with open(GEOJSON_FILE, 'r') as f:
        gj = json.load(f)
    
    parcels_data = []
    for i, feat in enumerate(gj['features']):
        p_id = feat['properties'].get('id', f"P{i}")
        p_nombre = feat['properties'].get('nombre', p_id)
        
        # LOCALIZACIÓN
        coords = feat['geometry']['coordinates'][0]
        lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
        padding = 0.002
        bbox = [min(lons)-padding, min(lats)-padding, max(lons)+padding, max(lats)+padding]
        
        img_pnoa = get_wms_image(bbox, "PNOA", WMS_PNOA, f"pnoa_{p_id}.png")
        img_sigpac = get_wms_image(bbox, "PARCELA", WMS_SIGPAC, f"sigpac_{p_id}.png")
        img_topo = get_wms_image(bbox, "MTN", "https://www.ign.es/wms-inspire/ign-base", f"topo_{p_id}.png")
        
        # DATOS
        stats_file = run_sentinel_api(i, p_id, "2025-10-01T00:00:00Z", "2026-04-01T00:00:00Z")
        chart_path = generate_multi_index_chart(stats_file, p_id)
        
        # FUNCIÓN AUXILIAR PARA RESOLVER RUTAS (Prioriza GeoJSON > Descarga)
        def resolve_img(prop_key, default_file):
            custom_path = feat['properties'].get(prop_key)
            if custom_path and os.path.exists(custom_path):
                return f"file://{os.path.abspath(custom_path)}"
            return f"file://{default_file.absolute()}" if default_file and default_file.exists() else ""

        parcels_data.append({
            "info": {"id": p_id, "nombre": p_nombre},
            "wms": {
                "pnoa": resolve_img("path_pnoa", img_pnoa),
                "sigpac": resolve_img("path_sigpac", img_sigpac),
                "topo": resolve_img("path_topo", img_topo)
            },
            "fisiografia": {
                "altitud": "450 m", "pendiente_pct": "4.5%", "pendiente_deg": "2.6°",
                "orientacion": "Sureste (SE)", "superficie": f"{calculate_surface(feat['geometry'])} ha",
                "municipio": feat['properties'].get('municipio', 'N/D'),
                "poligono": feat['properties'].get('poligono', 'N/D')
            },
            "indices": {
                "ndvi": resolve_img("path_ndvi", RASTER_DIR / f"{p_id}_ndvi.png"),
                "ndre": resolve_img("path_ndre", RASTER_DIR / f"{p_id}_ndre.png"),
                "ndmi": resolve_img("path_ndmi", RASTER_DIR / f"{p_id}_ndmi.png")
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
    pdf_path = REPORTS_DIR / "informe_premium.pdf"
    HTML(string=html_out, base_url=str(PROJECT_ROOT)).write_pdf(pdf_path)
    print(f"Informe generado en: {pdf_path}")

if __name__ == "__main__":
    main()
