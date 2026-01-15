import json
import geopandas as gpd
from shapely.geometry import Polygon

def get_bucket_info(mm):
    # Standard USDA/NOHRSC Scale
    thresholds = [
        (10,    "#E0F7FA", "0-0.39 in"), (50,    "#B2EBF2", "0.39-2.0 in"),
        (100,   "#80DEEA", "2.0-3.9 in"), (250,   "#4DD0E1", "3.9-9.8 in"),
        (500,   "#0288D1", "9.8-20 in"),  (1000,  "#303F9F", "20-39 in"),
        (1500,  "#7B1FA2", "39-59 in"),  (2500,  "#C2185B", "59-98 in"),
        (5000,  "#FF4081", "98-197 in"), (7500,  "#F50057", "197-295 in"),
        (10000, "#D500F9", "295-394 in"),(20000, "#6200EA", "394-787 in")
    ]
    for i, (limit, color, label) in enumerate(thresholds):
        if mm <= limit: return i, color, label
    return 11, "#6200EA", "787+ in"

def create_contiguous_dissolve(input_file, output_file):
    HALF_SIZE = 0.00833333 / 2
    
    with open(input_file, 'r') as f:
        data = json.load(f)

    temp_features = []
    for p in data.get('data', []):
        lat, lon, depth = p['lat'], p['lon'], p['depth_mm']
        if depth < 2: continue 

        bucket_id, hex_color, label = get_bucket_info(depth)
        square = Polygon([
            (lon - HALF_SIZE, lat - HALF_SIZE), (lon - HALF_SIZE, lat + HALF_SIZE),
            (lon + HALF_SIZE, lat + HALF_SIZE), (lon + HALF_SIZE, lat - HALF_SIZE)
        ])

        temp_features.append({
            "geometry": square, "b": bucket_id, "c": hex_color, "label": label
        })

    # 1. Create GeoDataFrame
    gdf = gpd.GeoDataFrame(temp_features)

    # 2. Dissolve by Bucket (Merges everything in a bucket into one MultiPolygon)
    dissolved = gdf.dissolve(by='b', aggfunc={'c': 'first', 'label': 'first'})

    # 3. Explode (Breaks MultiPolygons into separate rows if they are NOT touching)
    # index_parts=False ensures we get a clean flat index back
    contiguous_gdf = dissolved.explode(index_parts=False).reset_index()

    # 4. Save to GeoJSON
    contiguous_gdf.to_file(output_file, driver='GeoJSON')
    print(f"Done! Created {len(contiguous_gdf)} contiguous snow islands.")

create_contiguous_dissolve('snow_depth.json', 'contiguous_snow_islands.geojson')
