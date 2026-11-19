---
name: gis-files
description: Use when the user shares or mentions a GIS file (Shapefile .shp or a zip of .shp/.shx/.dbf/.prj, KML, KMZ, GeoJSON) and wants to open, read, inspect, summarize, convert, map, or plan work from it, e.g. "what's in this shapefile", "convert this KML to GeoJSON", "show this route on a map", "how many miles of fiber is this".
---

# Working with GIS files

The Harmis GIS connector reads KML, KMZ, GeoJSON and Shapefile. Pick the tool by what the user wants:

| User wants | Tool |
|---|---|
| What is in the file: layers, feature counts, geometry types, CRS, extent, total line length, attribute fields | `read_gis_file` |
| The file in another format: GeoJSON, KML, or CSV (attributes + WKT geometry) | `convert_gis_file` |
| To see the shapes | `preview_map` |
| To track build progress on the features (routes, sites, areas) | `create_harmis_project` |

## Workflow

1. Start with `read_gis_file` unless the user asked only for a conversion or a map. Report layers, feature counts, geometry types and the attribute fields that matter for the question (e.g. footage, status, owner).
2. Answer the actual question from the summary: line length is in feet, convert to miles when the user speaks in miles.
3. Offer `preview_map` when the user would benefit from seeing the geometry; call it right away when they ask to see or map it.
4. Call `create_harmis_project` only when the user asks to track, plan or manage work on the file. It needs a Harmis account; the user is asked to sign in the first time.

## File rules

- A Shapefile is several files. Ask for a zip holding at least `.shp`, `.shx`, `.dbf` and `.prj`; a lone `.shp` cannot be read.
- Files up to 20 MB. A conversion result over 1 MB is refused: suggest filtering or splitting the file.
- Coordinates must be WGS 84 (EPSG:4326, the KML/GeoJSON default). A projected file (e.g. State Plane, UTM) is named in the summary but not reprojected; tell the user to export it in WGS 84.
- GeoTIFF, GeoPackage and other formats are not supported; say so rather than guessing at the contents.
