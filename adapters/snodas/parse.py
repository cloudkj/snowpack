import numpy as np
import json
import os

def parse_snodas_v2(hdr_txt_path, dat_path, output_json):
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
            "point_count": len(points)
        },
        "data": points
    }

    with open(output_json, 'w') as f:
        json.dump(result, f)

    print(f"Done. Processed {len(points)} snow-covered points into {output_json}")

# Example Usage
parse_snodas_v2(
    'us_ssmv11036tS__T0001TTNATS2026011405HP001.txt',
    'us_ssmv11036tS__T0001TTNATS2026011405HP001.dat',
    'snow_depth.json'
)

#
#
