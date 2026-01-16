snowpack
========

Simple proof-of-concept for mashing up different sources of geo data onto a
single map. The motivating example is plotting popular ski destinations and
layering on the latest snow depth data. This prototype currently supports
adding points of interest data via KML files and additional data via GeoJSON
files.

## Demo

[California SNO-Parks](https://ohv.parks.ca.gov/?page_id=30701) Snow Depth
Report: [https://cloudkj.github.io/snowpack/examples/ca_sno_parks/](https://cloudkj.github.io/snowpack/examples/ca_sno_parks/)

## Usage

```javascript
import { initMap, loadKML, loadGeoJSON } from './src/snowpack.js';

initMap('map', { centerCoords: [39.5, -120.5], zoomLevel: 8 });

const kmlUrl = ...;
const kmlPropNames = { ... };
await loadKML(kmlUrl, kmlPropNames);

const geoJsonUrl = ...;
const geoJsonPropNames = { ... };
await loadGeoJSON(geoJsonUrl, geoJsonPropNames);
```

## Examples

### Data Sources

* Points of interest
* Heatmaps
  * National Snow and Ice Data Center (NSIDC) Snow Data: https://nsidc.org/data/g02158/versions/1
  * USGS Earthquakes: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php

For points of interest, a common source of user-generated data is the My Maps
interface within Google Maps, which allows users to create custom maps and export
markers as KML/KMZ files.

For heatmaps, some data sources require custom adapter logic to parse, format,
and convert the data into the GeoJSON format.

### Snow Depth Data Example

As part of the prototype for displaying snow depth data from NSIDC, we provide an
[example adapter](adapters/snodas/generate.py) that is able to download and
[convert](https://nsidc.org/sites/default/files/g02158-v001-userguide_2_1.pdf)
NSIDC Snow Data Assimilation System (SNODAS) [data](https://noaadata.apps.nsidc.org/NOAA/G02158/)
into GeoJSON files.
