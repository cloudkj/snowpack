snowpack
========

Simple proof-of-concept for mashing up different sources of geo data onto a
single map. An example is plotting popular ski destinations and layering out the
latest snow depth data. The prototype currently supports adding points of
interest data via KML files and heatmap data via GeoJSON files.

# Data Sources

* Points of interest
  * 
* Heatmaps
  * National Snow and Ice Data Center (NSIDC) Snow Data: https://nsidc.org/data/g02158/versions/1
  * USGS Earthquakes: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php

For points of interest, a common source of user-generated data is the My Maps UI
within Google Maps, which allows users to create custom maps and export markers
as KML/KMZ files.

For heatmaps, some data sources require custom adapter logic to parse, format,
and convert the data into the GeoJSON format.

## Example

For snow depth data from NSIDC, we provide an example adapter that is able to
downlaod and [convert](https://nsidc.org/sites/default/files/g02158-v001-userguide_2_1.pdf)
NSIDC Snow Data Assimilation System (SNODAS) [data](https://noaadata.apps.nsidc.org/NOAA/G02158/)
into GeoJSON files.
