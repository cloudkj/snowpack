import os
import tarfile
import gzip
import requests
import argparse
import shutil
import sys
import numpy as np
import json
import geopandas as gpd
from shapely.geometry import Polygon

def download_and_extract(url, filter_string="1036"):
    local_tar = "temp_snodas.tar"
    extract_dir = "extracted_snodas"
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    print(f"Downloading: {url}")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_tar, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

    print("Download complete. Extracting...")

    try:
        with tarfile.open(local_tar, "r") as tar:
            members = [m for m in tar.getmembers() if filter_string in m.name]
            
            if not members:
                print(f"No files found matching '{filter_string}'")
                return
            
            decompressed = []
            for member in members:
                print(f"Extracting: {member.name}")
                tar.extract(member, path=extract_dir)
                compressed_path = os.path.join(extract_dir, member.name)

                if compressed_path.endswith('.gz'):
                    decompressed_path = compressed_path[:-3]
                    
                    print(f"  Decompressing: {member.name}")
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(decompressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    os.remove(compressed_path)
                    decompressed.append(decompressed_path)
            
            header_file = next((f for f in decompressed if f.endswith('.txt')), None)
            data_file = next((f for f in decompressed if f.endswith('.dat')), None)
            parse_snodas_v2(header_file, data_file)
                    
    finally:
        # 4. Cleanup the large tar file
        if os.path.exists(local_tar):
            os.remove(local_tar)
            print("Temporary archive removed.")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
            print("Extract directory removed.")

def parse_snodas_v2(hdr_txt_path, dat_path):
    """
    Parses SNODAS .dat files using instructions from NSIDC G02158 User Guide.
    """
    
    # 1. Parse Metadata from the .txt file provided by NOHRSC/NSIDC
    # The guide notes that ncols=6935 and nrows=3351 for masked CONUS data.
    meta = {}
    with open(hdr_txt_path, 'r') as f:
        for line in f:
            if ':' in line:
                key, val = line.split(':', 1)
                meta[key.strip().lower()] = val.strip()
    print(meta)

    # Mapping NSIDC/NOHRSC header keys to variables
    # If keys vary, these defaults match the official 1km CONUS grid
    ncols = int(meta.get('number of columns', 6935))
    nrows = int(meta.get('number of rows', 3351))
    ulx = float(meta.get('benchmark x-axis coordinate', -124.729583333333))
    uly = float(meta.get('benchmark y-axis coordinate', 52.8704166666666))
    xdim = float(meta.get('x-axis resolution', 0.00833333333333333))
    ydim = float(meta.get('y-axis resolution', 0.00833333333333333))
    date = ''.join([
        meta.get('created year'),
        meta.get('created month').zfill(2),
        meta.get('created day').zfill(2),
    ])
    nodata = -9999

    # 2. Read Binary Data
    # NSIDC Spec: 16-bit signed integer, Big-Endian ('>i2')
    try:
        # np.fromfile is the most reliable way to read raw binary grids
        raw_data = np.fromfile(dat_path, dtype='>i2')
        
        # Validate file size (2 bytes per pixel)
        expected_size = ncols * nrows
        if raw_data.size != expected_size:
            raise ValueError(f"File size mismatch. Expected {expected_size} pixels, found {raw_data.size}")
            
        grid = raw_data.reshape((nrows, ncols))
    except Exception as e:
        print(f"Error reading binary file: {e}")
        return
    print(grid.shape)

    # 3. Extract points with snow (Value > 0)
    # This filters out 'no data' (-9999) and 'no snow' (0)
    rows, cols = np.where(grid > 0)
    
    # Calculate Lat/Lon using the grid parameters
    # Lat = Top - (row * cell_height)
    # Lon = Left + (col * cell_width)
    lats = uly - (rows * ydim)
    lons = ulx + (cols * xdim)
    depths = grid[rows, cols]

    # 4. Create JSON Structure
    points = []
    for i in range(len(depths)):
        points.append({
            "lat": round(float(lats[i]), 6),
            "lon": round(float(lons[i]), 6),
            "depth_mm": int(depths[i])
        })

    result = {
        "metadata": {
            "file": os.path.basename(dat_path),
            "description": "NOHRSC SNODAS Snow Depth",
            "units": "millimeters",
            "point_count": len(points),
            "date": date
        },
        "data": points
    }

    metadata_json = f"metadata_{date}.json"
    with open(metadata_json, 'w') as f:
        json.dump(result["metadata"], f)

    print(f"Processed {len(points)} points and wrote metadata to {metadata_json}")

    create_contiguous_dissolve(points, f"snodas_snow_depth_{date}.geojson")

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

def create_contiguous_dissolve(points, output_file):
    # Standard SNODAS resolution
    RES = 0.00833333
    # We add a tiny 'fudge factor' to the half-size to ensure overlap
    HALF_SIZE = (RES + 0.000005) / 2

    temp_features = []
    for p in points:
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

    contiguous_gdf['geometry'] = contiguous_gdf['geometry'].buffer(0)

    # 4. Save to GeoJSON
    contiguous_gdf.to_file(output_file, driver='GeoJSON')
    print(f"Created {len(contiguous_gdf)} contiguous polygonal features.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and parse SNODAS tar files.")
    parser.add_argument("url", help="The full URL to the .tar file")
    
    args = parser.parse_args()
    download_and_extract(args.url)
