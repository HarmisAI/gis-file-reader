# GIS File Reader by Harmis

Open GIS files in Claude without desktop GIS software. Share a Shapefile (as a zip), KML, KMZ or
GeoJSON file and ask about it: Claude reads its layers, feature counts, geometry types, coordinate
system, extent, total line length and attribute fields; converts it to GeoJSON, KML or CSV; and
shows the shapes on an interactive map.

For telecom and fiber teams, a route or design file can become a Harmis project that tracks
build progress per route, site and area, once you sign in to a Harmis account.

## What this plugin contains

- **Connector**: the Harmis GIS connector at `https://api.harmis.com/mcp`. The file you share is
  sent to that server to be read; reading, converting and mapping need no account.
  Creating a project needs a Harmis account and sends the file's features to your workspace.
- **Skill `gis-files`**: tells Claude which tool fits the request and the file rules (zipped
  Shapefiles, 20 MB limit, WGS 84 coordinates).

The plugin runs no local code and installs nothing.

## Privacy

See https://www.harmis.com/privacy.

## Support

hello@harmis.com
