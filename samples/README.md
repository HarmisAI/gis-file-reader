# Sample files

Files to try GIS File Reader with. They describe Maple Ridge, a fiber-to-the-home build for a
subdivision that does not exist. The streets, the conduit, the vaults and the build phases are
made up: `generate.py` draws them on open farmland in Dallas County, Iowa. No file here holds
data from a real network, a real design or a map provider.

| File | Format | What GIS File Reader finds in it |
|---|---|---|
| [maple-ridge-conduit.shp.zip](https://raw.githubusercontent.com/HarmisAI/gis-file-reader/main/samples/maple-ridge-conduit.shp.zip) | Shapefile, zipped | 134 conduit segments, 31,883 ft in all. Each has its street, conduit size, placement, length, phase and the vaults at its ends |
| [maple-ridge-conduit.kml](https://raw.githubusercontent.com/HarmisAI/gis-file-reader/main/samples/maple-ridge-conduit.kml) | KML | The same conduit segments |
| [maple-ridge-vaults.geojson](https://raw.githubusercontent.com/HarmisAI/gis-file-reader/main/samples/maple-ridge-vaults.geojson) | GeoJSON | 120 vaults and hand holes as points. Each has its type, street, lid rating and phase |
| [maple-ridge-phases.geojson](https://raw.githubusercontent.com/HarmisAI/gis-file-reader/main/samples/maple-ridge-phases.geojson) | GeoJSON | 5 build phases as areas. Each has its status, start month, conduit footage and vault count |

Coordinates are WGS 84 in every file.

## Try one

Each file name above is a link that downloads the file itself. Copy the link, give it to Claude
and ask in your own words:

```
What's in this shapefile?
https://raw.githubusercontent.com/HarmisAI/gis-file-reader/main/samples/maple-ridge-conduit.shp.zip
```

```
Show these vaults on a map:
https://raw.githubusercontent.com/HarmisAI/gis-file-reader/main/samples/maple-ridge-vaults.geojson
```

## Make the files again

```
python3 samples/generate.py
```

The script needs only Python 3 and has nothing random in it: the same streets, names and numbers
come out each time.

## License

MIT, like the rest of this repository. See [LICENSE](../LICENSE).
