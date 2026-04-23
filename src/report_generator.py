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
WMS_CATASTRO = "https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx"
WMS_TOPO = "https://www.ign.es/wms-inspire/ign-base"

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
        img_pnoa = get_wms_image(bbox_mid, "OI.OrthoimageCoverage", WMS_PNOA, f"pnoa_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        img_topo = get_wms_image(bbox_wide, "IGNBaseTodo", WMS_TOPO, f"topo_{p_id}_{mes_actual}.png", output_dir=WMS_OUT)
        
        # Foto de límites (Overlay)
        path_overlay = WMS_OUT / f"overlay_{p_id}_{mes_actual}.png"
        img_sigpac = overlay_geometry(img_pnoa, parcel, bbox_mid, path_overlay)
        
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
