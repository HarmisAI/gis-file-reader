# GIS File Reader by Harmis

Open GIS files in Claude without desktop GIS software. Give Claude a Shapefile (as a zip), KML,
KMZ or GeoJSON file and ask about it. Claude reads its layers, feature counts, geometry types,
coordinate system, extent, total line length and attribute fields; converts it to GeoJSON, KML or
CSV; and shows the shapes on an interactive map in the chat.

For telecom and fiber teams, a route or design file can become a Harmis project that tracks build
progress per route, site and area, once you sign in to a Harmis account.

## Set up

### Claude

1. Open [Customize > Connectors](https://claude.ai/customize/connectors).
2. Add a custom connector with this address: `https://api.harmis.com/mcp`
3. In a chat, turn the connector on from **+ > Connectors**.

On Team and Enterprise plans an Owner adds the connector for the organization.

No sign-in is needed to read, convert or map a file. Claude asks you to sign in to Harmis only
when you ask it to create a project.

### Claude Code

Add the connector alone:

```
claude mcp add --transport http harmis-gis https://api.harmis.com/mcp
```

Or load the plugin in this repository, which adds the connector and a skill that tells Claude
which tool fits the request:

```
git clone https://github.com/HarmisAI/gis-file-reader.git
claude --plugin-dir gis-file-reader/gis-file-reader
```

## Use

Give Claude a link to the file: an `https` address that opens without a sign-in. Then ask in your
own words.

| Ask | What you get |
|---|---|
| "What's in this shapefile? `<link>`" | Layers, feature counts, geometry types, coordinate system, extent, total line length, attribute fields |
| "How many miles of fiber is in this file?" | The total line length, from the same summary |
| "Convert this KML to GeoJSON" | The file in GeoJSON, KML, or CSV with WKT geometry |
| "Show this route on a map" | The shapes on an interactive map in the chat |
| "Create a Harmis project from this file" | A Harmis project that tracks progress on the file's routes, sites and areas (needs a Harmis account) |

## Tools

| Tool | What it does | Changes anything? |
|---|---|---|
| `read_gis_file` | Summarizes the file | No |
| `convert_gis_file` | Returns the file as GeoJSON, KML or CSV | No |
| `preview_map` | Shows the shapes on a map | No |
| `create_harmis_project` | Creates a project in your Harmis workspace from the file's features | Yes, after you sign in |

## File rules

- **Formats:** Shapefile, KML, KMZ, GeoJSON. GeoTIFF, GeoPackage and other formats are not read.
- **Shapefile:** a zip that holds at least the `.shp`, `.shx`, `.dbf` and `.prj`. A lone `.shp`
  cannot be read.
- **Size:** up to 20 MB. A conversion result over 1 MB is refused; filter or split the file.
- **Coordinates:** WGS 84 (EPSG:4326, the KML and GeoJSON default). A projected file (State Plane,
  UTM) is named in the summary but not reprojected; export it in WGS 84 first.

## What is sent where

The file you give is sent to the Harmis server at `https://api.harmis.com/mcp` to be read. When
you give a link, that server downloads the file from the link. Creating a project sends the
file's features to your Harmis workspace. The plugin runs no local code and installs nothing.

- Privacy: https://www.harmis.com/privacy
- Terms: https://www.harmis.com/terms

## Support

hello@harmis.com

## License

MIT. See [LICENSE](LICENSE).
