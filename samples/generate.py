#!/usr/bin/env python3
"""Writes the sample files of this folder. Standard library only, and nothing random in it.

Maple Ridge is made up: a fiber-to-the-home build for a subdivision that does not exist. The
streets are drawn by this script on open land, so no file here holds data from a real network,
a real design or a map provider.

    python3 samples/generate.py
"""

import json
import math
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent

# The south-west corner of the subdivision, WGS 84: a field in Dallas County, Iowa, east of
# K Avenue, with no road or building on it.
ORIGIN_LAT = 41.6905
ORIGIN_LON = -94.0855
EARTH_RADIUS_M = 6_371_008.8  # the mean radius, the sphere lengths are measured on
METERS_PER_DEGREE = math.radians(1) * EARTH_RADIUS_M
FEET_PER_METER = 3.28084

MIDDLE = 520.0  # phases A lie west of it, phases B east
EDGE_EAST = 1200.0
EDGE_NORTH = 930.0
VAULT_SPACING = 90.0
VERTEX_SPACING = 15.0

# The plat, in meters east and north of the origin. An east-west street bends around a base
# northing; it runs between two cross streets, or from a point where it ends on its own.
#   name, base northing, bend, wavelength, shift, from, to
EAST_WEST_STREETS = [
    ("Sugar Maple Dr", 85.0, 18.0, 1500.0, 0.4, "Ridgeline Pkwy", "Samara Blvd"),
    ("Red Maple Ln", 225.0, 14.0, 1100.0, 2.0, "Sapwood Way", "Samara Blvd"),
    ("Maple Ridge Pkwy", 385.0, 30.0, 1700.0, 3.6, -65.0, "Samara Blvd"),
    ("Boxelder Ln", 540.0, 16.0, 1300.0, 1.1, "Ridgeline Pkwy", "Hickory St"),
    ("Sycamore Dr", 680.0, 20.0, 1000.0, 5.0, "Ridgeline Pkwy", "Samara Blvd"),
    ("Heartwood Ln", 830.0, 15.0, 1600.0, 2.7, "Catkin Way", "Samara Blvd"),
]
# A cross street bends around a base easting and runs from one east-west street to another.
#   name: base easting, bend, shift, first street, last street (indexes of the list above)
CROSS_STREETS = {
    "Ridgeline Pkwy": (60.0, 10.0, 0.0, 0, 4),
    "Sapwood Way": (250.0, 8.0, 1.5, 0, 2),
    "Catkin Way": (250.0, 6.0, 4.0, 4, 5),
    "Canopy Way": (430.0, 9.0, 3.0, 2, 4),
    "Linden St": (610.0, 8.0, 0.8, 0, 3),
    "Alder St": (790.0, 7.0, 2.2, 3, 5),
    "Hickory St": (965.0, 9.0, 5.1, 1, 4),
    "Samara Blvd": (1140.0, 12.0, 3.9, 0, 5),
}
# A court leaves a street and ends: name, street index, easting, +1 north or -1 south, length.
COURTS = [
    ("Aspen Ct", 0, 330.0, -1, 55.0),
    ("Birch Ct", 0, 760.0, -1, 60.0),
    ("Willow Ct", 0, 890.0, 1, 62.0),
    ("Cedar Ct", 1, 430.0, 1, 64.0),
    ("Hazel Ct", 4, 540.0, 1, 60.0),
    ("Acorn Ct", 5, 500.0, 1, 55.0),
    ("Juniper Ct", 5, 980.0, 1, 50.0),
]
COURT_LEAN = 0.18  # a court is not square to its street
ENTRANCE = "Maple Ridge Pkwy"  # it starts at K Avenue, the county road, and carries the feeder
FEEDER_STREETS = {ENTRANCE, "Linden St"}
ARTERIALS = {ENTRANCE, "Ridgeline Pkwy", "Samara Blvd"}

PHASES = {
    "1A": {"status": "Built", "start": "2026-09"},
    "1B": {"status": "In construction", "start": "2026-11"},
    "2A": {"status": "Permitted", "start": "2027-03"},
    "2B": {"status": "Designed", "start": "2027-05"},
    "3": {"status": "Designed", "start": "2027-08"},
}

WGS84_PRJ = (
    'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
    'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
)
ZIP_DATE = (2026, 11, 20, 0, 0, 0)


def street_y(index, x):
    """The northing of east-west street `index` at easting `x`."""
    _, base, bend, wavelength, shift, _, _ = EAST_WEST_STREETS[index]
    return base + bend * math.sin(2 * math.pi * x / wavelength + shift)


def cross_x(name, y):
    """The easting of cross street `name` at northing `y`."""
    base, bend, shift, _, _ = CROSS_STREETS[name]
    return base + bend * math.sin(2 * math.pi * y / 900.0 + shift)


def crossing(index, name):
    """The easting where east-west street `index` and cross street `name` meet."""
    x = CROSS_STREETS[name][0]
    for _ in range(60):  # both streets bend gently, so this settles in a few rounds
        x = cross_x(name, street_y(index, x))
    return x


def ends_of(index):
    """The eastings where east-west street `index` starts and ends."""
    return [
        crossing(index, end) if isinstance(end, str) else end
        for end in EAST_WEST_STREETS[index][5:]
    ]


def meets(index, name):
    """Whether east-west street `index` and cross street `name` have a junction."""
    first, last = CROSS_STREETS[name][3:]
    start, end = ends_of(index)
    return first <= index <= last and start - 0.5 <= crossing(index, name) <= end + 0.5


def to_lon_lat(point):
    x, y = point
    lat = ORIGIN_LAT + y / METERS_PER_DEGREE
    lon = ORIGIN_LON + x / (METERS_PER_DEGREE * math.cos(math.radians(ORIGIN_LAT)))
    return [round(lon, 6), round(lat, 6)]


def length_of(line):
    return sum(math.dist(a, b) for a, b in zip(line, line[1:]))


def feet_along(lon_lat_line):
    """The length a GIS measures on the written coordinates: great-circle, in feet."""
    meters = 0.0
    for (lon_a, lat_a), (lon_b, lat_b) in zip(lon_lat_line, lon_lat_line[1:]):
        lat_a, lat_b, turn = math.radians(lat_a), math.radians(lat_b), math.radians(lon_b - lon_a)
        half_chord = (
            math.sin((lat_b - lat_a) / 2) ** 2
            + math.cos(lat_a) * math.cos(lat_b) * math.sin(turn / 2) ** 2
        )
        meters += 2 * EARTH_RADIUS_M * math.asin(math.sqrt(half_chord))
    return meters * FEET_PER_METER


def phase_at(point):
    x, y = point
    south_limit = (street_y(1, x) + street_y(2, x)) / 2
    north_limit = (street_y(3, x) + street_y(4, x)) / 2
    if y >= north_limit:
        return "3"
    side = "A" if x < MIDDLE else "B"
    return ("1" if y < south_limit else "2") + side


def runs():
    """Every street as (name, the stops where it meets another street or ends, its path)."""
    result = []
    for index, street in enumerate(EAST_WEST_STREETS):
        stops = set(ends_of(index))
        stops.update(crossing(index, name) for name in CROSS_STREETS if meets(index, name))
        stops.update(x for _, parent, x, _, _ in COURTS if parent == index)
        result.append((street[0], sorted(stops), lambda x, i=index: (x, street_y(i, x))))
    for name in CROSS_STREETS:
        stops = sorted(
            street_y(index, crossing(index, name))
            for index in range(len(EAST_WEST_STREETS))
            if meets(index, name)
        )
        result.append((name, stops, lambda y, n=name: (cross_x(n, y), y)))
    for name, parent, x, heading, length in COURTS:
        y = street_y(parent, x)
        result.append(
            (
                name,
                [0.0, length],
                lambda t, x=x, y=y, h=heading: (x + COURT_LEAN * t, y + h * t),
            )
        )
    return result


def build_network():
    """The vaults by position and the conduit segments between them, in street order."""
    vaults = {}
    segments = []

    def vault_at(point, street, is_junction):
        key = (round(point[0], 1), round(point[1], 1))
        vault = vaults.setdefault(key, {"point": point, "streets": [], "junction": False})
        vault["streets"].append(street)
        vault["junction"] = vault["junction"] or is_junction
        return vault

    for street, stops, path in runs():
        for start, end in zip(stops, stops[1:]):
            steps = max(2, math.ceil((end - start) / VERTEX_SPACING))
            piece = [path(start + (end - start) * step / steps) for step in range(steps + 1)]
            parts = math.ceil(length_of(piece) / VAULT_SPACING)
            for part in range(parts):
                a = start + (end - start) * part / parts
                b = start + (end - start) * (part + 1) / parts
                vertices = max(1, math.ceil((b - a) / VERTEX_SPACING))
                line = [path(a + (b - a) * v / vertices) for v in range(vertices + 1)]
                segments.append(
                    {
                        "street": street,
                        "line": line,
                        "from": vault_at(line[0], street, part == 0),
                        "to": vault_at(line[-1], street, part == parts - 1),
                    }
                )
    ordered = sorted(vaults.values(), key=lambda v: (round(v["point"][1] / 40), v["point"][0]))
    for number, vault in enumerate(ordered, start=1):
        vault["name"] = f"MR-V-{number:03d}"
    return ordered, segments


def conduit_rows(segments):
    rows = []
    for number, segment in enumerate(segments, start=1):
        line = segment["line"]
        street = segment["street"]
        is_feeder = street in FEEDER_STREETS
        phase = phase_at(line[len(line) // 2] if len(line) > 2 else midpoint(line))
        if street.endswith(" Ct"):
            placement = "Open trench"
        elif is_feeder:
            placement = "Directional bore"
        else:
            placement = "Joint trench"
        rows.append(
            {
                "NAME": f"MR-C-{number:03d}",
                "STREET": street,
                "CONDUIT": "2 in HDPE" if is_feeder else "1.25 in HDPE",
                "DUCTS": 2 if is_feeder else 1,
                "PLACEMENT": placement,
                "LENGTH_FT": round(feet_along([to_lon_lat(point) for point in line]), 1),
                "PHASE": phase,
                "STATUS": PHASES[phase]["status"],
                "FROM_VAULT": segment["from"]["name"],
                "TO_VAULT": segment["to"]["name"],
            }
        )
    return rows


def midpoint(line):
    (ax, ay), (bx, by) = line[0], line[-1]
    return ((ax + bx) / 2, (ay + by) / 2)


def vault_properties(vault):
    streets = sorted(set(vault["streets"]), key=vault["streets"].index)
    on_feeder = any(street in FEEDER_STREETS for street in streets)
    if vault["junction"] and on_feeder:
        kind = "Vault 30x48"
    elif vault["junction"] and len(streets) > 1:
        kind = "Hand hole 24x36"
    else:
        kind = "Hand hole 17x30"
    phase = phase_at(vault["point"])
    return {
        "name": vault["name"],
        "VAULT_TYPE": kind,
        "STREET": " & ".join(streets[:2]),
        "SPLICE": "Yes" if vault["junction"] and len(streets) > 1 else "No",
        "LID_RATING": "Tier 22" if any(s in ARTERIALS for s in streets) else "Tier 15",
        "PHASE": phase,
        "STATUS": PHASES[phase]["status"],
    }


def phase_rings():
    """Each phase's outline, counter-clockwise: block limits run halfway between two streets."""

    def limit(lower, upper):
        return lambda x: (street_y(lower, x) + street_y(upper, x)) / 2

    south, north = limit(1, 2), limit(3, 4)
    bottom, top = (lambda x: 0.0), (lambda x: EDGE_NORTH)
    areas = {
        "1A": (0.0, MIDDLE, bottom, south),
        "1B": (MIDDLE, EDGE_EAST, bottom, south),
        "2A": (0.0, MIDDLE, south, north),
        "2B": (MIDDLE, EDGE_EAST, south, north),
        "3": (0.0, EDGE_EAST, north, top),
    }
    rings = {}
    for phase, (west, east, low, high) in areas.items():
        steps = round((east - west) / 60.0)
        xs = [west + (east - west) * step / steps for step in range(steps + 1)]
        ring = [(x, low(x)) for x in xs] + [(x, high(x)) for x in reversed(xs)]
        rings[phase] = ring + [ring[0]]
    return rings


def write_geojson(path, features):
    lines = ",\n".join(json.dumps(feature, separators=(",", ":")) for feature in features)
    path.write_text('{"type":"FeatureCollection","features":[\n' + lines + "\n]}\n")


def write_kml(path, layer, rows, lines):
    fields = [name for name in rows[0] if name != "NAME"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>']
    out.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    out.append(f"<Document><name>{escape(layer)}</name>")
    out.append(f'<Schema name="{escape(layer)}" id="{escape(layer)}">')
    for name in fields:
        kind = {int: "int", float: "float"}.get(type(rows[0][name]), "string")
        out.append(f'<SimpleField name="{name}" type="{kind}"/>')
    out.append("</Schema>")
    for row, line in zip(rows, lines):
        data = "".join(
            f'<SimpleData name="{name}">{escape(str(row[name]))}</SimpleData>' for name in fields
        )
        coordinates = " ".join(f"{lon},{lat}" for lon, lat in line)
        out.append(
            f"<Placemark><name>{escape(row['NAME'])}</name>"
            f'<ExtendedData><SchemaData schemaUrl="#{escape(layer)}">{data}</SchemaData>'
            f"</ExtendedData><LineString><coordinates>{coordinates}</coordinates></LineString>"
            "</Placemark>"
        )
    out.append("</Document></kml>")
    path.write_text("\n".join(out) + "\n")


def shp_header(shape_type, length_words, box):
    return (
        struct.pack(">i5ii", 9994, 0, 0, 0, 0, 0, length_words)
        + struct.pack("<ii4d4d", 1000, shape_type, *box, 0.0, 0.0, 0.0, 0.0)
    )


def box_of(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def shapefile_parts(rows, lines):
    """The .shp, .shx and .dbf of a PolyLine layer (ESRI Shapefile Technical Description, 1998)."""
    polyline = 3
    records, index, offset = b"", b"", 50
    for number, line in enumerate(lines, start=1):
        content = struct.pack("<i4dii", polyline, *box_of(line), 1, len(line))
        content += struct.pack("<i", 0)
        content += b"".join(struct.pack("<2d", lon, lat) for lon, lat in line)
        words = len(content) // 2
        records += struct.pack(">ii", number, words) + content
        index += struct.pack(">ii", offset, words)
        offset += 4 + words
    box = box_of([point for line in lines for point in line])
    shp = shp_header(polyline, offset, box) + records
    shx = shp_header(polyline, 50 + len(index) // 2, box) + index

    fields = []
    for name in rows[0]:
        values = [row[name] for row in rows]
        if isinstance(values[0], str):
            fields.append((name, b"C", max(len(v.encode()) for v in values), 0))
        else:
            decimals = 1 if isinstance(values[0], float) else 0
            fields.append((name, b"N", max(len(str(v)) for v in values), decimals))
    record_length = 1 + sum(width for _, _, width, _ in fields)
    year, month, day = ZIP_DATE[:3]
    dbf = struct.pack(
        "<4BIHH20x", 3, year - 1900, month, day, len(rows), 33 + 32 * len(fields), record_length
    )
    for name, kind, width, decimals in fields:
        dbf += struct.pack("<11sc4xBB14x", name.encode(), kind, width, decimals)
    dbf += b"\r"
    for row in rows:
        dbf += b" "
        for name, kind, width, _ in fields:
            text = str(row[name]).encode()
            dbf += text.rjust(width) if kind == b"N" else text.ljust(width)
    dbf += b"\x1a"
    return shp, shx, dbf


def write_shapefile_zip(path, layer, rows, lines):
    shp, shx, dbf = shapefile_parts(rows, lines)
    parts = {"shp": shp, "shx": shx, "dbf": dbf, "prj": WGS84_PRJ.encode(), "cpg": b"UTF-8"}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for extension, content in parts.items():
            entry = zipfile.ZipInfo(f"{layer}.{extension}", ZIP_DATE)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, content)


def main():
    vaults, segments = build_network()
    rows = conduit_rows(segments)
    lines = [[to_lon_lat(point) for point in segment["line"]] for segment in segments]

    write_shapefile_zip(HERE / "maple-ridge-conduit.shp.zip", "maple-ridge-conduit", rows, lines)
    write_kml(HERE / "maple-ridge-conduit.kml", "maple-ridge-conduit", rows, lines)

    vault_features = [
        {
            "type": "Feature",
            "properties": vault_properties(vault),
            "geometry": {"type": "Point", "coordinates": to_lon_lat(vault["point"])},
        }
        for vault in vaults
    ]
    write_geojson(HERE / "maple-ridge-vaults.geojson", vault_features)

    phase_features = []
    for phase, ring in phase_rings().items():
        in_phase = [row for row in rows if row["PHASE"] == phase]
        phase_features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": f"Phase {phase}",
                    "PHASE": phase,
                    "STATUS": PHASES[phase]["status"],
                    "START": PHASES[phase]["start"],
                    "CONDUIT_FT": round(sum(row["LENGTH_FT"] for row in in_phase)),
                    "VAULTS": sum(1 for v in vault_features if v["properties"]["PHASE"] == phase),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[to_lon_lat(point) for point in ring]],
                },
            }
        )
    write_geojson(HERE / "maple-ridge-phases.geojson", phase_features)

    print(f"{len(rows)} conduit segments, {sum(row['LENGTH_FT'] for row in rows):,.0f} ft")
    print(f"{len(vault_features)} vaults, {len(phase_features)} phases")


if __name__ == "__main__":
    main()
